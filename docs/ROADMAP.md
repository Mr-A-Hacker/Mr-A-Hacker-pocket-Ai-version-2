# Pocket AI — Project Roadmap

This roadmap suggests future improvements for Pocket AI. Items below are planned ideas, not a guarantee that they are implemented in the current build.

## Assistant experience
- [ ] Add a first-run setup checklist for models, audio devices, and optional tools.
- [ ] Make model download progress, size, and errors easy to understand.
- [ ] Add clear controls to export or delete conversation history.
- [ ] Provide a low-resource mode for devices with limited RAM.

## Voice and vision
- [ ] Add a microphone and speaker test page.
- [ ] Explain when camera and microphone access are active.
- [ ] Add configurable image retention and a one-click gallery cleanup option.
- [ ] Show a clear message when optional vision hardware or models are unavailable.

## Developer experience
- [ ] Add automated tests for core Python utilities.
- [ ] Add a dependency/setup troubleshooting guide for Raspberry Pi and Linux.
- [ ] Document supported Python and Node.js versions in one place.
- [ ] Add a diagnostic command that checks required dependencies without exposing secrets.

## Privacy and reliability
- [ ] Keep local conversation data and credentials out of Git.
- [ ] Make online-only features clearly identify when they need a connection.
- [ ] Add graceful handling for missing model files and unavailable audio devices.
- [ ] Document which features run locally and which contact external services.
