// src/index.js
import express from "express";
import session from "express-session";
import cors from "cors";
import dotenv from "dotenv";
import jwt from "jsonwebtoken";

import passport from "./passport.js";

dotenv.config();

const {
  PORT = 4000,
  SESSION_SECRET = "supersecret",
  JWT_SECRET = "jwtsecret",
} = process.env;

const app = express();

app.use(cors({ origin: true, credentials: true }));
app.use(express.json());
app.use(
  session({
    secret: SESSION_SECRET,
    resave: false,
    saveUninitialized: false,
  })
);
app.use(passport.initialize());
app.use(passport.session());

// Helper to generate JWT token from user profile
function generateToken(user) {
  return jwt.sign(
    {
      provider: user.provider,
      id: user.id,
      displayName: user.displayName,
      emails: user.emails,
    },
    JWT_SECRET,
    { expiresIn: "12h" }
  );
}

// Generic route factory for each provider
function buildAuthRoutes(provider, scope = []) {
  // Redirect to provider
  app.get(`/auth/${provider}`, passport.authenticate(provider, { scope }));

  // Callback
  app.get(
    `/auth/${provider}/callback`,
    passport.authenticate(provider, {
      failureRedirect: "/auth/failure",
      session: false,
    }),
    (req, res) => {
      const token = generateToken(req.user);
      // For SPA redirect with token or just respond JSON
      res.json({ token, user: req.user });
    }
  );
}

buildAuthRoutes("google", ["profile", "email"]);
buildAuthRoutes("facebook", ["email"]);
buildAuthRoutes("instagram");
buildAuthRoutes("linkedin");

// Failure
app.get("/auth/failure", (_req, res) => {
  res.status(401).json({ error: "Authentication failed" });
});

app.get("/", (_req, res) => {
  res.send("Auth service is running");
});

app.listen(PORT, () => console.log(`Auth service listening on port ${PORT}`));
