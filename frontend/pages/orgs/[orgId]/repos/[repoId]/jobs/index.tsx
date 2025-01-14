import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { formatDistance } from "date-fns";

import { useRouter } from "next/router";
import { Job } from "../../../../../../models";
import {
  job as jobApi,
  org as orgApi,
  repo as repoApi,
} from "../../../../../../api";
import useUser from "../../../../../../lib/useUser";
import ErrorMessage from "../../../../../../components/ErrorMessage";
import LoadingPage from "../../../../../../components/LoadingPage";
import { index, noData } from "../../../../../../api/common";
import Breadcrumbs from "../../../../../../components/Breadcrumbs";
import { gql, useQuery } from '@apollo/client';

function runningTime(a: Job): number {
  const now = new Date();
  const updatedAt =
    a.status === "complete" || a.status === "canceled"
      ? new Date(a.updatedAt).getTime()
      : now.getTime(); // + now.getTimezoneOffset() * 60000;
  const createdAt = new Date(a.createdAt).getTime();
  return Math.round((updatedAt - createdAt) / 1000);
}

function RunningTime({ a }: { a: Job }) {
  const [time, setTime] = useState<number>(runningTime(a));

  useEffect(() => {
    if (a.status === "complete" || a.status === "canceled") return;
    const timeout = setInterval(() => setTime(runningTime(a)), 100);
    return () => clearInterval(timeout);
  }, [a]);

  return <span>{time}s</span>;
}

const LIST_JOBS = gql`
  query ListJobs($orgId: ID!, $repoId: ID!) {
    org(id: $orgId) {
      repo(repoId: $repoId) {
        jobs {
          id
          name
          status
          creatorId
          createdAt
          updatedAt
        }
      }
    }
  }
`;

export default function Index() {
  const { } = useUser();
  const router = useRouter();
  const { orgId, repoId } = router.query as { orgId?: string; repoId?: string };
  const { data, error: dataError, loading, startPolling } = useQuery(LIST_JOBS, { variables: { orgId: orgId, repoId: repoId } });
  const [error, setError] = useState<Error | undefined>(undefined);
  const api = jobApi(orgId, repoId);
  const [name, setName] = useState("");

  if (loading)
    return <LoadingPage />;
  if (dataError) return <ErrorMessage error={dataError} />;
  if (error) return <ErrorMessage error={error} setError={setError} />;
  if (!data) return null;

  const org = data.org;
  const repo = data.org.repo;
  const jobs: any[] = data.org.repo.jobs;

  const inputEmpty = !name.replaceAll(" ", "");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (inputEmpty) return;
    try {
      await api.create({ name });
      setName("");
      startPolling(500);
    } catch (e: any) {
      setError(e)
    }
  }

  function handleChange({ target: { value } }: ChangeEvent<HTMLInputElement>) {
    setName(value);
  }

  return (
    <>
      <Breadcrumbs
        pages={
          [
            { name: org.name, href: { pathname: "/orgs/[orgId]", query: { orgId } } },
            { name: repo.name, href: { pathname: "/orgs/[orgId]/repos/[repoId]", query: { orgId, repoId }, current: true } },
          ]
        }
      />

      <form className="mt-8" onSubmit={handleSubmit}>
        <label>
          Schedule job:{" "}
          <input
            type="text"
            value={name}
            placeholder="name"
            onChange={handleChange}
          />
        </label>{" "}
        <input type="submit" value="schedule" disabled={inputEmpty} />
      </form>

      <br />

      <table className="min-w-full divide-y divide-gray-300">
        <thead className="bg-gray-50">
          <tr>
            <th scope="col" className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-6">
              Name
            </th>
            <th
              scope="col"
              className="hidden sm:table-cell px-3 py-3.5 text-left text-sm font-semibold text-gray-900 "
            >
              Actor
            </th>
            <th scope="col" className="hidden lg:table-cell px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
              Started
            </th>
            <th scope="col" className="hidden sm:table-cell px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
              Duration
            </th>
            <th
              scope="col"
              className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900"
            >
              Status
            </th>
            <th scope="col" className="relative py-3.5 pl-3 pr-4 sm:pr-6">
              <span className="sr-only">Edit</span>
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white">
          {jobs.map((job) => (
            <tr key={job.id}>
              <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 sm:pl-6">
                {job.name}
              </td>
              <td className="hidden sm:table-cell whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                {job.creatorId}
              </td>
              <td className="hidden lg:table-cell  whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                {formatDistance(new Date(), new Date(job.createdAt))} ago
              </td>
              <td className="hidden sm:table-cell  whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                <RunningTime a={job} />
              </td>
              <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">{job.status}</td>
              <td className="whitespace-nowrap py-4 px-2 text-right text-sm font-medium sm:pr-6 w-16">
                {job.cancelable &&
                  <a href="#" onClick={(e) => { e.preventDefault(); api.cancel(job.id) }} className="text-red-600 hover:text-red-900">
                    Cancel<span className="sr-only">, {job.id}</span>
                  </a>
                }
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}