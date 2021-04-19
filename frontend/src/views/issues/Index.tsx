import { useContext, useEffect, useState } from 'react';
import { Link, RouteComponentProps } from '@reach/router';

import { Issue, Org, Repo } from '../../models';
import { issue as issueApi, org as orgApi, repo as repoApi } from '../../api';
import { NotifyContext, UserContext } from '../../App';

interface IndexProps extends RouteComponentProps {
  orgId?: string;
  repoId?: string;
}

export function Index({ orgId, repoId }: IndexProps) {
  const user = useContext(UserContext);
  const { error } = useContext(NotifyContext);
  const [org, setOrg] = useState<Org>();
  const [repo, setRepo] = useState<Repo>();
  const [issues, setIssues] = useState<Issue[]>();

  useEffect(() => {
    orgApi.show(orgId).then(setOrg).catch(error);
  }, [orgId]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    repoApi.show(orgId, repoId).then(setRepo).catch(error);
  }, [orgId, repoId]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    issueApi.index(orgId, repoId).then(setIssues).catch(error);
  }, [orgId, repoId]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!org || !repo || !issues) return null;

  const maybeNewLink = !user.loggedIn() ? null : (
    <Link to={`/orgs/${orgId}/repos/${repoId}/issues/new`}>
      Create new issue
    </Link>
  );

  return (
    <>
      <h1>
        <Link to={`/orgs/${org.id}`}>{org.name}</Link> /{' '}
        <Link to={`/orgs/${org.id}/repos/${repo.id}`}>{repo.name}</Link> /
        issues
      </h1>
      <ul>
        {issues.map((i) => (
          <li key={'issue-' + i.id}>
            <Link to={`/orgs/${org.id}/repos/${repo.id}/issues/${i.id}`}>
              #{i.id} - {i.title}
            </Link>
          </li>
        ))}
      </ul>
      {maybeNewLink}
    </>
  );
}
