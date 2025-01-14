import { ChangeEvent, FormEvent, useContext, useState } from "react";

import { session as sessionApi } from "../api";
import { useRouter } from "next/router";
import useUser from "../lib/useUser";
import ErrorPage from "../components/ErrorMessage";

export default function Login() {
  const { currentUser, setUsername } = useUser({ redirectIfFound: true });
  const router = useRouter();
  const [login, setLogin] = useState<string>("");

  const api = sessionApi();

  const [error, setError] = useState<Error | undefined>(undefined);
  if (error) return <ErrorPage error={error} setError={setError} />

  // If a logged-in user navigates to this page, redirect to home.
  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    api.login(login == "" ? {} : { username: login }).then(u => {
      setUsername(u.username);
      router.replace(`/orgs`);
    }).catch(e => setError(e));
  }


  function handleChange({ target: { value } }: ChangeEvent<HTMLInputElement>) {
    setLogin(value);
  }

  return (
    <>
      <div className="min-h-full pb-16 flex flex-col justify-center sm:py-4 sm:px-6 lg:px-8">
        <div className="sm:mt-8 sm:mx-auto sm:w-full sm:max-w-md">
          <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
            <form className="space-y-6" onSubmit={handleSubmit}>
              <div>
                <label
                  htmlFor="username"
                  className="block text-sm font-medium text-gray-700"
                >
                  Username (leave empty to log in as a random user)
                </label>
                <div className="mt-1">
                  <input
                    id="username"
                    name="username"
                    type="username"
                    autoComplete="username"
                    required={false}
                    className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    value={login}
                    onChange={handleChange}
                  />
                </div>
                <span className="text-gray-300 text-sm">
                  Try logging in as &quot;john&quot;
                </span>
              </div>

              <div>
                <label
                  htmlFor="password"
                  className="block text-sm font-medium text-gray-700"
                >
                  Password
                </label>
                <div className="mt-1">
                  <input
                    id="password"
                    name="password"
                    type="password"
                    autoComplete="current-password"
                    required={false}
                    disabled
                    className="bg-gray-100 appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  />
                </div>
                <span className="text-gray-300 text-sm">
                  No passwords required in this demo!
                </span>
              </div>
              <div>
                <button
                  type="submit"
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Sign in
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </>
  );
}

Login.title = "Sign In";
