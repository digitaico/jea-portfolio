def areAnagrams(a, b):
    if len(a) != len(b):
        return False

    # Frequency character maps and compare
    char_q_a = {}
    char_q_b = {}

    for char in a:
        char_q_a[char] = char_q_a.get(char, 0) + 1

    for char in b:
        char_q_b[char] = char_q_b.get(char, 0) + 1

    return char_q_a == char_q_b

# Usage
print(f"'anagram' and 'margana' {areAnagrams('anagram', 'margana')}")
