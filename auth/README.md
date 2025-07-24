# Auth Service

This microservice provides **authentication & authorization** for your application using OAuth2 social logins.

Supported providers:

- Google (Gmail)
- Facebook
- Instagram
- LinkedIn

The service is built with **Node.js**, **Express**, and **Passport.js**.

---

## Quick Start

1. **Install dependencies**

   ```bash
   cd auth
   npm install
   ```

2. **Set environment variables**
   Create a `.env` file in `auth/` with at least:

   ```env
   PORT=4000
   BASE_URL=http://localhost:4000

   SESSION_SECRET=supersecret
   JWT_SECRET=jwtsecret

   # Google
   GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=xxxxxx

   # Facebook
   FACEBOOK_APP_ID=xxxxxx
   FACEBOOK_APP_SECRET=xxxxxx

   # Instagram
   INSTAGRAM_CLIENT_ID=xxxxxx
   INSTAGRAM_CLIENT_SECRET=xxxxxx

   # LinkedIn
   LINKEDIN_CLIENT_ID=xxxxxx
   LINKEDIN_CLIENT_SECRET=xxxxxx
   ```

3. **Run the server**
   ```bash
   npm start
   # or for hot-reload
   npm run dev
   ```

---

## API Endpoints

| Method | Path                       | Description                                |
| ------ | -------------------------- | ------------------------------------------ |
| GET    | `/auth/google`             | Redirect user to Google for authentication |
| GET    | `/auth/google/callback`    | Google redirects here after approval       |
| GET    | `/auth/facebook`           | Redirect to Facebook                       |
| GET    | `/auth/facebook/callback`  | Facebook OAuth callback                    |
| GET    | `/auth/instagram`          | Redirect to Instagram                      |
| GET    | `/auth/instagram/callback` | Instagram OAuth callback                   |
| GET    | `/auth/linkedin`           | Redirect to LinkedIn                       |
| GET    | `/auth/linkedin/callback`  | LinkedIn OAuth callback                    |

On successful authentication the callback returns a JSON payload:

```json
{
  "token": "<jwt>",
  "user": {
    /* basic profile */
  }
}
```

Use the JWT to authenticate subsequent requests from other services or clients.

---

## Extending

- Replace the in-memory user handling in `src/passport.js` with a proper database if needed.
- Adjust JWT payload or expiration in `src/index.js`.
- Add more OAuth providers by installing a Passport strategy and wiring similar routes.
