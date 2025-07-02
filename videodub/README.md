# Translator

## WHAT

A text, voice and video translator.

- User can talk and get translated audio say an audio file and audio reproduction..
- User can parse a text file and gets a translated file.
- User can upload a video, and gets the same video in any of these forms
  - Translated captions over video, original audio
  - Translated captions over video, translated audio
  - Translated voice over video.

## WHY

I'm creating any interesting project in my spare time. Choose this because of a current unsatisfied need of my wife at work.
Translators are expensive.

## EXPECTATIONS

Just learn, maybe explore the business side, like a translator focused on local market, sick people with hearing and
verbalizing issues. Say smokers with larynx issues, old people with hearing loss that can't afford hearing aids.
Let's enjoy the project, maybe something interesting will appear!

## HOW

### 1. Use Case: Translate video.

Given a video file or group of video files, as a user I want to

- upload all videos, bulk upload
- Choose incoming and outcoming languages
- Choose if use of captions
- Get all files translated and a report of tasks done, like minutes translated, characters.

#### Pseudocode

1. Upload all files.
2. Write a manifesto listing each file name, size, mime type and ordinal.
3. For each file.

   3.1. Extract audio, write audio file.

   3.2. Clean audio removing background noise.

   3.3. Speech Recognition and return translated and transcribed text.

   3.4. Read (Text To Speech) translated audio.

   3.5. Assemble translated audio to video.
