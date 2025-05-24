/*
 * A left rotation operation on an array shifts each of the array's elements 1
 * unit to the left. For example, if 2 left rotations are performed on array
 * [1,2,3,4,5], then the array would become [3,4,5,1,2]. Given an array a and a
 * number of rotations d, perform d left rotations on the array. Return the
 * updated array.
 * Example
 * const a = [1, 2, 3, 4, 5];
 * const d = 2;
 * Expected output [3,4,35,1,2]

 * const n = len(a)
 * 1. number of rotations = d % n
 * 2. split array in two parts and join last split + first_split.
 * last_spplit = a[nomber_of_rotations:]
 * first_split = a[:number_of_rotations]
*/

const rotateLeft = (a, d) => {
  const n = a.length;
  const rotations = d % n;
  const left_part = a.slice(rotations);
  const right_part = a.slice(0, rotations);
  return left_part.concat(right_part);
};

// Usage
const arr = [5, 29, 6, 11, 96, 24, 87, 6];
const d = 3;
const result = rotateLeft(arr, d)

console.log(`Original: ${arr} rotations = ${d} -> Result: ${result}`)
