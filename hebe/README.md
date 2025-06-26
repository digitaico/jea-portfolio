# PROJECT HEBE

This is a computer vision DNN application that solves the problem of people who are older than 40 and is rejected in human
resources interviews due to non-written policies of rejecting old people, mainly in tech industry. So HEBE removes on real
time age signatures like marionette lines, Gladder lines and forehead lines. I ta can be fine tuned to remove under eye
bags.
It's use is not recommended to pass like a younger person, instead to show that hirers are biased just by a number, instead
of evaluating attitude and capabilities.

## Workflow

1. Capture Video
2. Detect Face
3. Detect facial landmarks using mediaPipe 468 Face Mesh.
4. Define ROI
5. Mask detection
6. Apply image processing like InPainting, Hessian filter, edge enhancers.
7. Compose video

### Project Tree

| file                         | function                                                       |
| ---------------------------- | -------------------------------------------------------------- |
| 1. main_application.py       | Central orchestrator                                           |
| 2. camera_handler.py         | Video Capture, frames                                          |
| 3. virtual_camera_emitter.py | Manages Virtual Camera                                         |
| 4. face_detector.py          | face detection                                                 |
| 5. edges_detector.py         | detect noise, strokes, edges (wrinkles)                        |
| 6. roi_setter.py             | Creates ROIs                                                   |
| 7. mask_setter.py            | Build binary masks over detected edges                         |
| 8. filter.py                 | All possible filters to alter image: Gaussian Blur, InPainting |
| 9. frame_modificator.py      | Application of filters to each frame                           |
| 10. video_composition.py     | Rebuilds video and streams                                     |
