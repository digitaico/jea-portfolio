// src/passport.js
// Configure Passport strategies for Google, Facebook, Instagram, and LinkedIn OAuth2

import passport from "passport";
import { Strategy as GoogleStrategy } from "passport-google-oauth20";
import { Strategy as FacebookStrategy } from "passport-facebook";
import { Strategy as InstagramStrategy } from "passport-instagram";
import { Strategy as LinkedInStrategy } from "passport-linkedin-oauth2";
import dotenv from "dotenv";

dotenv.config();

const {
  GOOGLE_CLIENT_ID,
  GOOGLE_CLIENT_SECRET,
  FACEBOOK_APP_ID,
  FACEBOOK_APP_SECRET,
  INSTAGRAM_CLIENT_ID,
  INSTAGRAM_CLIENT_SECRET,
  LINKEDIN_CLIENT_ID,
  LINKEDIN_CLIENT_SECRET,
  BASE_URL = "http://localhost:4000",
} = process.env;

/**
 * Generic verify callback for social strategies.
 * Just passes the profile on. In real-world use you would look up / create a user in DB.
 */
function verify(_, __, profile, done) {
  // In a production app, you'd store / fetch user from database here
  done(null, profile);
}

// Google
if (GOOGLE_CLIENT_ID && GOOGLE_CLIENT_SECRET) {
  passport.use(
    new GoogleStrategy(
      {
        clientID: GOOGLE_CLIENT_ID,
        clientSecret: GOOGLE_CLIENT_SECRET,
        callbackURL: `${BASE_URL}/auth/google/callback`,
      },
      verify
    )
  );
}

// Facebook
if (FACEBOOK_APP_ID && FACEBOOK_APP_SECRET) {
  passport.use(
    new FacebookStrategy(
      {
        clientID: FACEBOOK_APP_ID,
        clientSecret: FACEBOOK_APP_SECRET,
        callbackURL: `${BASE_URL}/auth/facebook/callback`,
        profileFields: ["id", "emails", "name", "displayName"],
      },
      verify
    )
  );
}

// Instagram (Basic Display API)
if (INSTAGRAM_CLIENT_ID && INSTAGRAM_CLIENT_SECRET) {
  passport.use(
    new InstagramStrategy(
      {
        clientID: INSTAGRAM_CLIENT_ID,
        clientSecret: INSTAGRAM_CLIENT_SECRET,
        callbackURL: `${BASE_URL}/auth/instagram/callback`,
      },
      verify
    )
  );
}

// LinkedIn
if (LINKEDIN_CLIENT_ID && LINKEDIN_CLIENT_SECRET) {
  passport.use(
    new LinkedInStrategy(
      {
        clientID: LINKEDIN_CLIENT_ID,
        clientSecret: LINKEDIN_CLIENT_SECRET,
        callbackURL: `${BASE_URL}/auth/linkedin/callback`,
        scope: ["r_liteprofile", "r_emailaddress"],
      },
      verify
    )
  );
}

// Serialize / deserialize user (minimal)
passport.serializeUser((user, done) => {
  done(null, user);
});
passport.deserializeUser((obj, done) => {
  done(null, obj);
});

export default passport;
