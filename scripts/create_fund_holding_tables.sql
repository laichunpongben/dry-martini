
CREATE TABLE funds (
  id           SERIAL PRIMARY KEY,
  fund_name    TEXT NOT NULL,
  report_date  DATE NOT NULL
);

CREATE TABLE securities (
  id                SERIAL PRIMARY KEY,
  security_name     TEXT NOT NULL,
  cusip             VARCHAR(12),
  isin              VARCHAR(15),
  sedol             VARCHAR(12)
);

CREATE TABLE fund_holdings (
  id                SERIAL PRIMARY KEY,
  fund_id           INTEGER NOT NULL REFERENCES funds(id),
  security_id       INTEGER NOT NULL REFERENCES securities(id),
  pct_of_portfolio  NUMERIC(7,4)
);
