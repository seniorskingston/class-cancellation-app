# Development environment and rollback

The live Class Cancellation site is unchanged. This work sits on the `development` branch. Do not merge that branch into `main`, and do not deploy it to the live Render services, unless Rebecca approves it.

## What is already protected

- Stable tag: `stable-2026-11-18`
- Live branch: `main` at that same commit
- Development branch: `development`
- The new function lives in `features/new_function/` and is off until `FEATURE_NEW_FUNCTION=true`
- With `APP_ENV=test`, the app does not send email and does not start the daily or weekly reports
- With `APP_ENV=test`, the app stops immediately if `SUPABASE_URL` contains the production project `ptyqolpecpqebuzwwcsn`

## Separate test database

1. Open https://supabase.com/dashboard and sign in.
2. Click **New project**. Give it a name such as `class-cancellation-test`. Do not open the existing production project for this step.
3. After it finishes creating, open **SQL Editor**, paste the contents of `supabase/migrations/20261117190300_initial_schema.sql`, and run it. This creates empty tables. Do not copy production records into them.
4. Open **Project Settings → API**. Copy the project URL and the secret key for this new project only.
5. Put those two values only in the test Render service, in the steps below. Do not replace the values on the live backend.

## Separate test website on Render

1. Open https://dashboard.render.com and sign in.
2. Click **New → Blueprint**.
3. Choose the repository `seniorskingston/class-cancellation-app`.
4. Set the branch to `development`.
5. When Render asks for the blueprint file, choose `render.test.yaml`. If it only offers `render.yaml`, cancel and use the manual path below instead. Do not apply `render.test.yaml` to the existing live services.
6. When Render asks for `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`, paste the **test** project values from the step above.
7. Wait until both new services are live. Their names are `class-cancellation-backend-test` and `class-cancellation-frontend-test`.
8. Open `https://class-cancellation-backend-test.onrender.com/api/environment`. It should say `"app_env": "test"`, `"emails_enabled": false`, and `"new_function": false`.

### Manual path if Blueprint is not available

Create two new services. Leave the existing live services alone.

Backend:

- Name: `class-cancellation-backend-test`
- Branch: `development`
- Build command: `pip install -r requirements.txt`
- Start command: `python -m uvicorn backend_sqlite:app --host 0.0.0.0 --port $PORT`
- Environment variables: `APP_ENV=test`, `EMAILS_ENABLED=false`, `SCHEDULED_ACTIONS_ENABLED=false`, `FEATURE_NEW_FUNCTION=false`, plus the test `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`

Frontend:

- Name: `class-cancellation-frontend-test`
- Branch: `development`
- Build command: `cd frontend && npm install && npm run build`
- Publish directory: `frontend/build`
- `REACT_APP_API_URL=https://class-cancellation-backend-test.onrender.com/api`
- `REACT_APP_FEATURE_NEW_FUNCTION=false`

## Turning the new function on

On the **test** backend only, set `FEATURE_NEW_FUNCTION` to `true` and redeploy that test service. The live site does not read this branch, so it stays off there. Set the value back to `false` to hide the new function again.

## Checks before any future merge

Run this from the project folder on the `development` branch:

```
python -m unittest tests.test_app_environment
```

Then, on the test website only:

- Open the public cancellation page and confirm the current programs still appear.
- Open the events calendar and confirm the current events still appear.
- Open the admin page and upload a file only if you intend to change the **test** database.
- Send a test inquiry and confirm no email arrives.
- Open `/api/environment` and confirm emails and scheduled jobs are off.

Do these checks before asking to merge `development` into `main`.

## Rollback

The live site is still the tagged version. If a later deployment of the live site goes wrong:

1. Open the live backend service in Render, not the test service.
2. Open **Manual Deploy**.
3. Deploy commit `9f2a22a`, which is tag `stable-2026-11-18`.
4. Repeat that for the live frontend service.
5. Do not change the live `SUPABASE_URL` or secret key while rolling back.

Deleting the test Render services, or the test Supabase project, does not remove the live site or the live records. Merging `development` into `main` is a separate decision and needs approval first.
