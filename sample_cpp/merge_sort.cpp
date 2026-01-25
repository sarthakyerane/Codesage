/**
 * Merge Sort Implementation
 * Classic divide-and-conquer sorting algorithm.
 * Time: O(n log n), Space: O(n)
 */
#include <iostream>
#include <vector>
using namespace std;

void merge(vector<int>& arr, int left, int mid, int right) {
    int n1 = mid - left + 1;
    int n2 = right - mid;

    vector<int> leftArr(n1), rightArr(n2);

    for (int i = 0; i < n1; i++) leftArr[i] = arr[left + i];
    for (int j = 0; j < n2; j++) rightArr[j] = arr[mid + 1 + j];

    int i = 0, j = 0, k = left;
    while (i < n1 && j < n2) {
        if (leftArr[i] <= rightArr[j]) arr[k++] = leftArr[i++];
        else arr[k++] = rightArr[j++];
    }
    while (i < n1) arr[k++] = leftArr[i++];
    while (j < n2) arr[k++] = rightArr[j++];
}

void mergeSort(vector<int>& arr, int left, int right) {
    if (left >= right) return;
    int mid = left + (right - left) / 2;
    mergeSort(arr, left, mid);
    mergeSort(arr, mid + 1, right);
    merge(arr, left, mid, right);
}

void printArray(const vector<int>& arr, const string& label) {
    cout << label << ": ";
    for (int x : arr) cout << x << " ";
    cout << "\n";
}

int countInversions(vector<int> arr) {
    // Count number of inversions using merge sort
    int n = arr.size();
    int count = 0;
    // Simplified: O(n^2) for demo, real implementation modifies merge step
    for (int i = 0; i < n; i++)
        for (int j = i + 1; j < n; j++)
            if (arr[i] > arr[j]) count++;
    return count;
}

int main() {
    vector<int> arr = {64, 25, 12, 22, 11, 90, 3, 47};
    printArray(arr, "Before");
    cout << "Inversions before sort: " << countInversions(arr) << "\n";

    mergeSort(arr, 0, arr.size() - 1);
    printArray(arr, "After ");
    cout << "Inversions after sort: " << countInversions(arr) << "\n";

    return 0;
}
