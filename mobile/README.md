# Readning Mobile

A simple React Native (Expo) client for the Readning API. It lets you select a text or PDF file, uploads it to the FastAPI server, and plays the generated background music.

## Requirements
- Node.js
- Expo CLI (`npm install -g expo-cli`)

## Development
```bash
cd mobile
npm install
npm start # then use Expo Go or a simulator
```

Update `API_BASE` in `App.tsx` with the address of your running FastAPI server.
