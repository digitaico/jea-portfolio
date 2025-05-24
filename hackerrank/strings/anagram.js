const areAnagrams =
    (a, b) => {
      if (a.length != b.length) {
        return false;
      }

      const char_q_a = new Map();
      const char_q_b = new Map();

      for (const char of a) {
        char_q_a.set(char, (char_q_a.get(char) || 0) + 1);
      };

      for (const char of b) {
        char_q_b.set(char, (char_q_b.get(char) || 0) + 1);
      }

      if (char_q_a.size !== char_q_b.size) {
        return false;
      }

      for (const [char, count] of char_q_a) {
        if (char_q_b.get(char) !== count) {
          return false;
        }
      }
      return true;
    }

              // Usage
              console.log(`amagrams = ${areAnagrams('anagram', 'margana')}`)
