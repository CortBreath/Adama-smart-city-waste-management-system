"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/auth/login",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            username,
            password,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Login failed");
      }

      localStorage.setItem("access_token", data.access_token);

      router.push("/");
    } catch (err) {
      console.error(err);

      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Unable to connect to the authentication server.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-page">

      {/* =====================================================
          REAL ADAMA CITY BACKGROUND
          ===================================================== */}

      <img
        src="/images/adama-city.jpg"
        alt=""
        className="city-background"
      />

      {/* Soft overlay over the photograph */}
      <div className="background-overlay" />

      {/* =====================================================
          LOGIN CARD
          ===================================================== */}

      <section className="login-card">

        {/* Brand */}
        <div className="brand">

          <div className="brand-logo" aria-label="Recycling">
            <span>♻</span>
          </div>

          <div className="brand-text">
            <h1>Adama Smart City</h1>
            <p>Smart Waste Management System</p>
          </div>

        </div>

        {/* Login heading */}
        <div className="login-heading">
          <h2>Administrator Login</h2>
          <p>Sign in to your account to continue</p>
        </div>

        {/* Error */}
        {error && (
          <div className="error-message" role="alert">
            {error}
          </div>
        )}

        {/* =====================================================
            LOGIN FORM
            ===================================================== */}

        <form onSubmit={handleLogin}>

          {/* Username */}
          <div className="form-group">

            <label htmlFor="username">
              Username
            </label>

            <div className="input-wrapper">

              <svg
                className="input-icon"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                aria-hidden="true"
              >
                <path
                  d="M20 21C20 17.6863 17.3137 15 14 15H10C6.68629 15 4 17.6863 4 21"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                />

                <circle
                  cx="12"
                  cy="7"
                  r="4"
                  stroke="currentColor"
                  strokeWidth="1.8"
                />
              </svg>

              <input
                id="username"
                type="text"
                value={username}
                onChange={(event) =>
                  setUsername(event.target.value)
                }
                placeholder="admin"
                autoComplete="username"
                required
              />

            </div>
          </div>

          {/* Password */}
          <div className="form-group password-group">

            <label htmlFor="password">
              Password
            </label>

            <div className="input-wrapper">

              <svg
                className="input-icon"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                aria-hidden="true"
              >
                <rect
                  x="5"
                  y="10"
                  width="14"
                  height="11"
                  rx="2"
                  stroke="currentColor"
                  strokeWidth="1.8"
                />

                <path
                  d="M8 10V7C8 4.79086 9.79086 3 12 3C14.2091 3 16 4.79086 16 7V10"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                />

                <circle
                  cx="12"
                  cy="15.5"
                  r="1.2"
                  fill="currentColor"
                />
              </svg>

              <input
                id="password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
                placeholder="Enter your password"
                autoComplete="current-password"
                required
              />

              <button
                type="button"
                className="password-toggle"
                onClick={() =>
                  setShowPassword((value) => !value)
                }
                aria-label={
                  showPassword
                    ? "Hide password"
                    : "Show password"
                }
              >
                {showPassword ? (
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                    aria-hidden="true"
                  >
                    <path
                      d="M2.5 12C4.4 7.8 7.6 5.5 12 5.5C16.4 5.5 19.6 7.8 21.5 12C19.6 16.2 16.4 18.5 12 18.5C7.6 18.5 4.4 16.2 2.5 12Z"
                      stroke="currentColor"
                      strokeWidth="1.8"
                    />

                    <circle
                      cx="12"
                      cy="12"
                      r="3"
                      stroke="currentColor"
                      strokeWidth="1.8"
                    />
                  </svg>
                ) : (
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                    aria-hidden="true"
                  >
                    <path
                      d="M3 3L21 21"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      strokeLinecap="round"
                    />

                    <path
                      d="M10.6 5.7C11.05 5.57 11.52 5.5 12 5.5C16.4 5.5 19.6 7.8 21.5 12C20.75 13.65 19.72 15 18.45 16"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      strokeLinecap="round"
                    />

                    <path
                      d="M6.25 6.65C4.65 7.8 3.4 9.6 2.5 12C4.4 16.2 7.6 18.5 12 18.5C13.15 18.5 14.2 18.3 15.15 17.95"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      strokeLinecap="round"
                    />
                  </svg>
                )}
              </button>

            </div>
          </div>

          {/* Sign In */}
          <button
            type="submit"
            disabled={loading}
            className="sign-in-button"
          >
            {loading ? (
              <>
                <span className="spinner" />
                Signing in...
              </>
            ) : (
              <>
                <svg
                  className="login-arrow"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                  aria-hidden="true"
                >
                  <path
                    d="M13 5L20 12L13 19"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />

                  <path
                    d="M20 12H4"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                  />
                </svg>

                Sign In
              </>
            )}
          </button>

        </form>

        {/* Secure access */}
        <div className="secure-access">

          <span className="secure-line" />

          <div className="secure-content">

            <svg
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              aria-hidden="true"
            >
              <path
                d="M12 3L19 6V11C19 15.5 16.1 19.2 12 21C7.9 19.2 5 15.5 5 11V6L12 3Z"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinejoin="round"
              />
            </svg>

            <span>Secure Access</span>

          </div>

          <span className="secure-line" />

        </div>

      </section>

      {/* =====================================================
          STYLES
          ===================================================== */}

      <style jsx>{`
        * {
          box-sizing: border-box;
        }

        .login-page {
          position: relative;

          min-height: 100vh;
          width: 100%;

          display: flex;
          align-items: center;
          justify-content: center;

          padding: 30px 20px;

          overflow: hidden;

          font-family:
            Inter,
            -apple-system,
            BlinkMacSystemFont,
            "Segoe UI",
            Roboto,
            Helvetica,
            Arial,
            sans-serif;
        }

        /* =====================================================
           CITY IMAGE
           ===================================================== */

        .city-background {
          position: absolute;

          inset: 0;

          width: 100%;
          height: 100%;

          object-fit: cover;

          /*
           * Keeps the important city area visible.
           */
          object-position: center center;

          z-index: 0;

          display: block;
        }

        /* =====================================================
           PHOTO OVERLAY
           ===================================================== */

        .background-overlay {
          position: absolute;

          inset: 0;

          z-index: 1;

          background:
            linear-gradient(
              135deg,
              rgba(236, 250, 246, 0.72) 0%,
              rgba(242, 251, 248, 0.45) 45%,
              rgba(225, 247, 241, 0.68) 100%
            );
        }

        /* =====================================================
           LOGIN CARD
           ===================================================== */

        .login-card {
          position: relative;

          z-index: 2;

          width: min(100%, 510px);

          padding: 34px 38px 27px;

          background: rgba(255, 255, 255, 0.97);

          border: 1px solid rgba(255, 255, 255, 0.95);

          border-radius: 22px;

          box-shadow:
            0 28px 70px rgba(20, 72, 68, 0.22),
            0 8px 25px rgba(20, 72, 68, 0.10);

          backdrop-filter: blur(8px);
        }

        /* =====================================================
           BRAND
           ===================================================== */

        .brand {
          display: flex;

          align-items: center;

          gap: 16px;

          margin-bottom: 28px;
        }

        .brand-logo {
          flex: 0 0 68px;

          width: 68px;
          height: 68px;

          display: flex;

          align-items: center;
          justify-content: center;

          border-radius: 18px;

          background:
            linear-gradient(
              135deg,
              #078f82 0%,
              #12b7a5 100%
            );

          box-shadow:
            0 10px 22px rgba(7, 143, 130, 0.25);
        }

        .brand-logo span {
          color: white;

          font-family: Arial, sans-serif;

          font-size: 42px;

          line-height: 1;

          font-weight: 400;
        }

        .brand-text {
          min-width: 0;
        }

        .brand-text h1 {
          margin: 0;

          color: #12345b;

          font-size: 29px;

          line-height: 1.12;

          font-weight: 750;

          letter-spacing: -0.8px;
        }

        .brand-text p {
          margin: 6px 0 0;

          color: #7183a0;

          font-size: 14px;

          line-height: 1.35;

          font-weight: 450;
        }

        /* =====================================================
           LOGIN HEADING
           ===================================================== */

        .login-heading {
          margin-bottom: 23px;
        }

        .login-heading h2 {
          margin: 0;

          color: #12345b;

          font-size: 24px;

          line-height: 1.2;

          font-weight: 700;

          letter-spacing: -0.4px;
        }

        .login-heading p {
          margin: 6px 0 0;

          color: #7183a0;

          font-size: 14px;

          line-height: 1.4;
        }

        /* =====================================================
           ERROR
           ===================================================== */

        .error-message {
          margin-bottom: 18px;

          padding: 11px 13px;

          border-radius: 9px;

          border: 1px solid #fecdca;

          background: #fff3f2;

          color: #b42318;

          font-size: 13px;

          line-height: 1.4;
        }

        /* =====================================================
           FORM
           ===================================================== */

        .form-group {
          margin-bottom: 17px;
        }

        .form-group label {
          display: block;

          margin-bottom: 7px;

          color: #173b63;

          font-size: 14px;

          line-height: 1.3;

          font-weight: 650;
        }

        .input-wrapper {
          position: relative;

          width: 100%;
        }

        .input-icon {
          position: absolute;

          left: 15px;
          top: 50%;

          width: 20px;
          height: 20px;

          transform: translateY(-50%);

          color: #7890aa;

          pointer-events: none;
        }

        .input-wrapper input {
          width: 100%;

          height: 52px;

          padding:
            0
            47px
            0
            46px;

          border: 1px solid #d5e0e9;

          border-radius: 10px;

          outline: none;

          background: rgba(255, 255, 255, 0.99);

          color: #344054;

          font-size: 15px;

          transition:
            border-color 0.2s ease,
            box-shadow 0.2s ease;
        }

        .input-wrapper input::placeholder {
          color: #8a98aa;

          opacity: 1;
        }

        .input-wrapper input:hover {
          border-color: #b8c9d8;
        }

        .input-wrapper input:focus {
          border-color: #0aa394;

          box-shadow:
            0 0 0 3px rgba(10, 163, 148, 0.11);
        }

        /* =====================================================
           PASSWORD
           ===================================================== */

        .password-group {
          margin-bottom: 22px;
        }

        .password-toggle {
          position: absolute;

          right: 9px;
          top: 50%;

          width: 34px;
          height: 34px;

          transform: translateY(-50%);

          display: flex;

          align-items: center;
          justify-content: center;

          padding: 0;

          border: none;

          border-radius: 7px;

          background: transparent;

          color: #7186a2;

          cursor: pointer;
        }

        .password-toggle:hover {
          background: #f0f8f6;

          color: #078f83;
        }

        .password-toggle svg {
          width: 20px;
          height: 20px;
        }

        /* =====================================================
           SIGN IN
           ===================================================== */

        .sign-in-button {
          width: 100%;

          height: 53px;

          display: flex;

          align-items: center;
          justify-content: center;

          gap: 9px;

          border: none;

          border-radius: 10px;

          background:
            linear-gradient(
              135deg,
              #078f82 0%,
              #10b8a5 100%
            );

          color: white;

          font-size: 16px;

          font-weight: 700;

          cursor: pointer;

          box-shadow:
            0 10px 22px rgba(8, 159, 144, 0.23);

          transition:
            transform 0.18s ease,
            box-shadow 0.18s ease;
        }

        .sign-in-button:hover:not(:disabled) {
          transform: translateY(-1px);

          box-shadow:
            0 13px 27px rgba(8, 159, 144, 0.28);
        }

        .sign-in-button:active:not(:disabled) {
          transform: translateY(0);
        }

        .sign-in-button:disabled {
          background: #86b9b2;

          cursor: not-allowed;

          box-shadow: none;
        }

        .login-arrow {
          width: 21px;
          height: 21px;
        }

        /* =====================================================
           LOADING
           ===================================================== */

        .spinner {
          width: 18px;
          height: 18px;

          border: 2px solid rgba(255, 255, 255, 0.4);

          border-top-color: white;

          border-radius: 50%;

          animation: spin 0.75s linear infinite;
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }

        /* =====================================================
           SECURE ACCESS
           ===================================================== */

        .secure-access {
          display: flex;

          align-items: center;

          gap: 12px;

          margin-top: 23px;
        }

        .secure-line {
          flex: 1;

          height: 1px;

          background: #dce5e9;
        }

        .secure-content {
          display: flex;

          align-items: center;

          gap: 7px;

          color: #7186a2;

          font-size: 12px;

          font-weight: 500;

          white-space: nowrap;
        }

        .secure-content svg {
          width: 18px;
          height: 18px;
        }

        /* =====================================================
           TABLET
           ===================================================== */

        @media (max-width: 700px) {
          .login-page {
            padding: 22px 15px;
          }

          .login-card {
            width: min(100%, 490px);

            padding: 30px 28px 25px;
          }

          .brand-logo {
            flex-basis: 62px;

            width: 62px;
            height: 62px;
          }

          .brand-logo span {
            font-size: 38px;
          }

          .brand-text h1 {
            font-size: 26px;
          }

          .brand-text p {
            font-size: 13px;
          }
        }

        /* =====================================================
           MOBILE
           ===================================================== */

        @media (max-width: 480px) {
          .login-page {
            min-height: 100svh;

            padding: 15px 12px;
          }

          .city-background {
            object-position: center center;
          }

          .background-overlay {
            background:
              linear-gradient(
                rgba(238, 251, 247, 0.82),
                rgba(238, 251, 247, 0.82)
              );
          }

          .login-card {
            width: 100%;

            padding: 25px 20px 22px;

            border-radius: 18px;
          }

          .brand {
            gap: 11px;

            margin-bottom: 24px;
          }

          .brand-logo {
            flex-basis: 57px;

            width: 57px;
            height: 57px;

            border-radius: 14px;
          }

          .brand-logo span {
            font-size: 35px;
          }

          .brand-text h1 {
            font-size: 22px;

            letter-spacing: -0.4px;
          }

          .brand-text p {
            margin-top: 4px;

            font-size: 11px;
          }

          .login-heading {
            margin-bottom: 21px;
          }

          .login-heading h2 {
            font-size: 21px;
          }

          .login-heading p {
            font-size: 13px;
          }

          .input-wrapper input {
            height: 51px;

            font-size: 14px;
          }

          .sign-in-button {
            height: 52px;

            font-size: 16px;
          }

          .secure-access {
            margin-top: 21px;
          }
        }
      `}</style>
    </main>
  );
}