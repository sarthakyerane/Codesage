CXX = g++
CXXFLAGS = -std=c++17 -O2 -Wall -Wextra
TARGET = analyzer

all: $(TARGET)

$(TARGET): analyzer.cpp
	$(CXX) $(CXXFLAGS) -o $(TARGET) analyzer.cpp

clean:
	rm -f $(TARGET)

.PHONY: all clean
