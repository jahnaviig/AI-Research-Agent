CREATE TABLE IF NOT EXISTS sessions (
  id UUID PRIMARY KEY,
  question TEXT NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'running',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS subtasks (
  id UUID PRIMARY KEY,
  session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  query TEXT NOT NULL,
  rationale TEXT NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS sources (
  id SERIAL PRIMARY KEY,
  session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
  subtask_id UUID REFERENCES subtasks(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  url TEXT NOT NULL,
  domain VARCHAR(255) NOT NULL,
  domain_score DOUBLE PRECISION NOT NULL,
  publish_date VARCHAR(64),
  content TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
  id SERIAL PRIMARY KEY,
  session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
  markdown TEXT NOT NULL,
  pdf_path TEXT,
  bibliography JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS agent_logs (
  id SERIAL PRIMARY KEY,
  session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
  agent VARCHAR(64) NOT NULL,
  status VARCHAR(32) NOT NULL,
  message TEXT NOT NULL,
  elapsed_ms INTEGER DEFAULT 0,
  payload JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

