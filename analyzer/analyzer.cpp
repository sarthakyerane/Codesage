/*
 Simple static analyzer for C++ files.
 Checks for common memory & safety issues.
 Outputs JSON to stdout so the API can parse it.
*/
#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <regex>

int main(int argc, char* argv[]) {
    if (argc < 2) { std::cerr << "usage: analyzer <file>\n"; return 1; }

    std::ifstream file(argv[1]);
    if (!file) { std::cerr << "cant open " << argv[1] << "\n"; return 1; }

    std::vector<std::string> lines;
    std::string line;
    while (std::getline(file, line)) lines.push_back(line);

    bool has_new = false, has_delete = false, has_fopen = false, has_fclose = false;
    std::string out = "[";
    int count = 0;

    for (int i = 0; i < (int)lines.size(); i++) {
        auto& l = lines[i];

        // memory leak check
        if (std::regex_search(l, std::regex(R"(\bnew\s)"))) has_new = true;
        if (l.find("delete") != std::string::npos) has_delete = true;

        // resource leak check
        if (l.find("fopen") != std::string::npos) has_fopen = true;
        if (l.find("fclose") != std::string::npos) has_fclose = true;

        // unsafe functions
        if (l.find("gets(") != std::string::npos) {
            if (count) out += ",";
            out += "{\"type\":\"buffer_overflow\",\"line\":" + std::to_string(i+1) + ",\"severity\":\"high\",\"detail\":\"gets() is unsafe, use fgets()\"}";
            count++;
        }
        if (l.find("strcpy(") != std::string::npos) {
            if (count) out += ",";
            out += "{\"type\":\"buffer_overflow\",\"line\":" + std::to_string(i+1) + ",\"severity\":\"medium\",\"detail\":\"strcpy has no bounds check, use strncpy\"}";
            count++;
        }
    }

    // report memory leak if new without delete
    if (has_new && !has_delete) {
        if (count) out += ",";
        out += "{\"type\":\"memory_leak\",\"line\":0,\"severity\":\"high\",\"detail\":\"new used without delete, possible memory leak\"}";
        count++;
    }
    if (has_fopen && !has_fclose) {
        if (count) out += ",";
        out += "{\"type\":\"resource_leak\",\"line\":0,\"severity\":\"high\",\"detail\":\"fopen without fclose, file handle leaked\"}";
        count++;
    }

    out += "]";
    std::cout << out << std::endl;
    // TODO: add uninit variable detection, float comparison check
    return 0;
}
