CREATE ROLE testuser NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT LOGIN;
ALTER USER testuser WITH PASSWORD 'test1234';

CREATE DATABASE ructfetest OWNER testuser;

