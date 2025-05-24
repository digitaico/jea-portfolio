import math

def hourglassSum(arr):
    maxHourglassSum = -math.inf

    for r in range(4):
        for c in range(4):
            currentSum = (arr[r][c] + arr[r][c + 1] + arr[r][c + 2] + arr[r + 1][c + 1] + arr[r + 2][c] + arr[r + 2][c + 1] + arr[r + 2][c + 2])

            if currentSum > maxHourglassSum:
                maxHourglassSum = currentSum

    return maxHourglassSum

# Usage
arr = [
  [1, 1, 1, 0, 0, 0],
  [0, 1, 0, 0, 0, 0],
  [1, 1, 1, 0, 0, 0],
  [0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0],
];
result = hourglassSum(arr);

print(f"Array :\n{arr}\nMax HourglassSum result: {result}")
