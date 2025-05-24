/*
 * A 6x6 array
 * Sum  all possible hourglasses :
 * a b c
 *   d
 * e f g
 * an hourglass is 3 rows tall and 3 columns wide
 */

const hourglassSum =
    (arr) => {
      let maxHourglassSum = -Infinity

      for (let r = 0; r <= 3; r++) {
        for (let c = 0; c <= 3; c++) {
          const currentSum =
              (arr[r][c] + arr[r][c + 1] + arr[r][c + 2] + arr[r + 1][c + 1] +
               arr[r + 2][c] + arr[r + 2][c + 1] + arr[r + 2][c + 2]);
          if (currentSum > maxHourglassSum) {
            maxHourglassSum = currentSum;
          }
        }
      };
      return maxHourglassSum;
      //--
    }

// Usage
const arr = [
  [1, 1, 1, 0, 0, 0],
  [0, 1, 0, 0, 0, 0],
  [1, 1, 1, 0, 0, 0],
  [0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0],
];
const result = hourglassSum(arr);

console.log(`Array :\n${
    arr.map(row => row.join(' ')).join('\n')}\nMax HourglassSum result: ${
    result}`)
