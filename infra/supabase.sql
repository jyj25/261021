-- Open single-workspace policy: every anonymous visitor can read and edit.
create table if not exists public.lab_workspace (
    id text primary key,
    payload jsonb not null default '{}'::jsonb,
    updated_at timestamptz not null default now()
);

alter table public.lab_workspace enable row level security;
grant select, insert, update, delete on public.lab_workspace to anon;

drop policy if exists "public can read lab workspace" on public.lab_workspace;
create policy "public can read lab workspace"
    on public.lab_workspace for select to anon using (true);

drop policy if exists "public can insert lab workspace" on public.lab_workspace;
create policy "public can insert lab workspace"
    on public.lab_workspace for insert to anon with check (true);

drop policy if exists "public can update lab workspace" on public.lab_workspace;
create policy "public can update lab workspace"
    on public.lab_workspace for update to anon using (true) with check (true);

drop policy if exists "public can delete lab workspace" on public.lab_workspace;
create policy "public can delete lab workspace"
    on public.lab_workspace for delete to anon using (true);

insert into public.lab_workspace (id, payload)
values ('main', '{}'::jsonb)
on conflict (id) do nothing;

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('lab-shared', 'lab-shared', true, 20971520, array['text/csv', 'text/plain', 'application/octet-stream'])
on conflict (id) do update set public = true, file_size_limit = 20971520;

drop policy if exists "public can read shared lab files" on storage.objects;
create policy "public can read shared lab files"
    on storage.objects for select to anon using (bucket_id = 'lab-shared');

drop policy if exists "public can upload shared lab files" on storage.objects;
create policy "public can upload shared lab files"
    on storage.objects for insert to anon with check (bucket_id = 'lab-shared');

drop policy if exists "public can update shared lab files" on storage.objects;
create policy "public can update shared lab files"
    on storage.objects for update to anon using (bucket_id = 'lab-shared') with check (bucket_id = 'lab-shared');

drop policy if exists "public can delete shared lab files" on storage.objects;
create policy "public can delete shared lab files"
    on storage.objects for delete to anon using (bucket_id = 'lab-shared');
