/**
 * BFS and DFS Graph Traversal
 * Standard implementations for demo and testing purposes.
 */
#include <iostream>
#include <vector>
#include <queue>
#include <stack>
using namespace std;

// ─── BFS: Breadth-First Search ────────────────────────────────────────────────
// Time: O(V+E), Space: O(V)
vector<int> bfs(vector<vector<int>>& graph, int start) {
    int n = graph.size();
    vector<bool> visited(n, false);
    vector<int> order;

    queue<int> q;
    q.push(start);
    visited[start] = true;

    while (!q.empty()) {
        int node = q.front();
        q.pop();
        order.push_back(node);

        for (int neighbor : graph[node]) {
            if (!visited[neighbor]) {
                visited[neighbor] = true;
                q.push(neighbor);
            }
        }
    }
    return order;
}

// ─── DFS: Depth-First Search (Iterative) ─────────────────────────────────────
// Time: O(V+E), Space: O(V)
vector<int> dfs_iterative(vector<vector<int>>& graph, int start) {
    int n = graph.size();
    vector<bool> visited(n, false);
    vector<int> order;

    stack<int> st;
    st.push(start);

    while (!st.empty()) {
        int node = st.top();
        st.pop();

        if (visited[node]) continue;
        visited[node] = true;
        order.push_back(node);

        // Push in reverse to maintain left-to-right order
        for (int i = graph[node].size() - 1; i >= 0; i--) {
            if (!visited[graph[node][i]]) {
                st.push(graph[node][i]);
            }
        }
    }
    return order;
}

// ─── DFS: Recursive ──────────────────────────────────────────────────────────
void dfs_recursive_helper(vector<vector<int>>& graph, int node,
                           vector<bool>& visited, vector<int>& order) {
    visited[node] = true;
    order.push_back(node);
    for (int neighbor : graph[node]) {
        if (!visited[neighbor]) {
            dfs_recursive_helper(graph, neighbor, visited, order);
        }
    }
}

vector<int> dfs_recursive(vector<vector<int>>& graph, int start) {
    int n = graph.size();
    vector<bool> visited(n, false);
    vector<int> order;
    dfs_recursive_helper(graph, start, visited, order);
    return order;
}

// ─── Check if Graph is Connected ─────────────────────────────────────────────
bool isConnected(vector<vector<int>>& graph) {
    if (graph.empty()) return true;
    vector<int> visited = bfs(graph, 0);
    return (int)visited.size() == (int)graph.size();
}

// ─── Count Connected Components ──────────────────────────────────────────────
int countComponents(vector<vector<int>>& graph) {
    int n = graph.size();
    vector<bool> visited(n, false);
    int components = 0;

    for (int i = 0; i < n; i++) {
        if (!visited[i]) {
            components++;
            // Mark all reachable nodes
            queue<int> q;
            q.push(i);
            visited[i] = true;
            while (!q.empty()) {
                int node = q.front();
                q.pop();
                for (int neighbor : graph[node]) {
                    if (!visited[neighbor]) {
                        visited[neighbor] = true;
                        q.push(neighbor);
                    }
                }
            }
        }
    }
    return components;
}

int main() {
    // Undirected graph: 6 vertices
    int n = 6;
    vector<vector<int>> graph(n);

    auto addEdge = [&](int u, int v) {
        graph[u].push_back(v);
        graph[v].push_back(u);
    };

    addEdge(0, 1); addEdge(0, 2);
    addEdge(1, 3); addEdge(2, 4);
    addEdge(3, 5);

    cout << "BFS from 0: ";
    for (int v : bfs(graph, 0)) cout << v << " ";
    cout << "\n";

    cout << "DFS from 0: ";
    for (int v : dfs_iterative(graph, 0)) cout << v << " ";
    cout << "\n";

    cout << "Connected: " << (isConnected(graph) ? "Yes" : "No") << "\n";
    cout << "Components: " << countComponents(graph) << "\n";

    return 0;
}
