// para cada letra del abecedario
// comparar si existe en le mapa de caracteres de cada array
// si no existe, asigne valor 0
// si existe en a y b, retorne INT(count_a - count_b)
// sume / acumule todos los deletions

const buildCharFrequency = (string) => {
  const charCounts = new Map();
  for (const char of string) {
    charCounts.set(char, (charCounts.get(char) || 0) + 1);
  }
  return charCounts;
};

const makeAnagram = (a, b) => {
  let totalDeletions = 0;
  const frequencyA = buildCharFrequency(a);
  const frequencyB = buildCharFrequency(b);

  // Get unique chars from each map
  const allChars = new Set([...frequencyA.keys(), ...frequencyB.keys()]);

  for (const char of allChars) {
    const countA = frequencyA.get(char) || 0;
    const countB = frequencyB.get(char) || 0;

    totalDeletions += Math.abs(countA - countB);
  }
  return totalDeletions;
};

const a = 'marimulatasiempreesasiporlatarde'
const b = 'vamonosdepaseoalxzaquebradaytraiganbicicletas'

console.log(`Deletions for\n${a}\n${b}\n${makeAnagram(a, b)}`)
