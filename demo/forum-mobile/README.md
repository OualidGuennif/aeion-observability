# Agora on React Native

The forum's front, on React Native 0.88.1 through Expo SDK 58, in TypeScript. Three screens and one
client:

| File | What it does |
| --- | --- |
| `App.tsx` | Routes between threads, session and compose; owns the session and the status line |
| `src/api.ts` | The whole network contract: health, threads, settings, register, login, logout, cookie |
| `src/screens/ThreadsScreen.tsx` | The list, readable without an account |
| `src/screens/SessionScreen.tsx` | Sign in, create the first account, or sign out |
| `src/screens/ComposeScreen.tsx` | Write a thread; a guest is sent to the session screen |
| `scripts/smoke.mjs` | Drives the compiled client against a live forum |

## Run it

```sh
cd demo/forum-mobile
npm install                       # 463 packages

# a forum to talk to, from demo/forum-app
AEION_SQLITE_PATH=/tmp/agora.db AGORA_SESSION_SECRET=<at least 32 bytes> \
  java -jar build/quarkus-app/quarkus-run.jar

npm start                         # Expo dev server; a simulator or a phone on the same network
EXPO_PUBLIC_AGORA_API=http://192.168.1.20:8081 npm start   # reach a forum on another host
```

The API base defaults to `http://127.0.0.1:8081`. On a physical device that address is the phone, not
your machine, so set `EXPO_PUBLIC_AGORA_API` to a reachable one.

## What was verified, and how

| Claim | Command | Result |
| --- | --- | --- |
| Types are sound | `npx tsc --noEmit` | exit 0 |
| It bundles for a device | `EXPO_NO_TELEMETRY=1 npx expo export --platform ios` | `iOS Bundled 5282ms index.ts (619 modules)`, 1.6 MB Hermes bundle |
| The client works against the real forum | `npm run smoke` | 12 steps passed: health, guest list, register, login (87-char signed cookie + 43-char CSRF token), create, read back, list contains it, 401 without a session, 401 on a wrong password, **403 without the CSRF token**, logout, 401 after revocation |

## What was not verified

- **No simulator or device run.** The bundle compiles and the network contract is proven, but no
  screenshot, gesture or layout has been checked on a screen. Treat the UI as unverified.
- **No UI test.** There is no Jest or Testing Library suite; the screens are covered only by the
  typechecker and the bundler.
- **The session is in memory only.** Closing the app signs you out. That is deliberate: a
  fifteen-minute session does not need to survive a restart, and a bearer value persisted on a phone
  is how a demo becomes a finding.
- **Reading a thread** navigates nowhere yet: `onOpen` is intentionally inert, so the list and the
  detail endpoint are proven by the smoke test rather than by a screen.

## Design notes

- **No navigation library.** Three screens managed by one `useState` do not justify
  `@react-navigation` and its dependencies; the route is a string.
- **The cookie is read explicitly.** React Native does not expose `Set-Cookie` consistently across
  platforms, so the client parses the login response and sends `Cookie: agora_session=...` itself.
- **Every mutation carries the CSRF token** the login returned, in `X-CSRF-Token`: holding the cookie
  alone is refused with 403 (feature 006).
- **Two planes stay separate.** The app never sends a worker's `aeion_...` gateway session. Those
  describe a build, not a person, and the API refuses them like any other unknown cookie.
