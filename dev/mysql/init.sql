CREATE TABLE platform_pkg_version (
  project_name  VARCHAR(100) NOT NULL,
  platform_name VARCHAR(100) NOT NULL,
  atm_version   VARCHAR(50)  NOT NULL,
  pkg_name      VARCHAR(100) NOT NULL,
  pkg_version   VARCHAR(50)  NOT NULL
);

CREATE TABLE platform_current_atm_version (
  project_name  VARCHAR(100) NOT NULL,
  platform_name VARCHAR(100) NOT NULL,
  atm_version   VARCHAR(50)  NOT NULL
);

CREATE TABLE csu_csms_relation (
  csu_name        VARCHAR(100) NOT NULL,
  csc_name        VARCHAR(100) NOT NULL,
  csci_name       VARCHAR(100) NOT NULL,
  css_name        VARCHAR(100) NOT NULL,
  csms_name       VARCHAR(100) NOT NULL,
  csu_description VARCHAR(100) NOT NULL
);

INSERT INTO platform_pkg_version (project_name, platform_name, atm_version, pkg_name, pkg_version) VALUES
  ('skywatch', 'nftw', '1.0.0', 'nav_app',    '1.0.0'),
  ('skywatch', 'nftw', '1.0.0', 'sensor_app', '1.0.0'),
  ('skywatch', 'nftw', '1.0.0', 'common_lib', '1.0.0'),
  ('skywatch', 'nftw', '1.0.0', 'system_repo', '1.0.0'),
  ('skywatch', 'nftw', '0.9.0', 'nav_app',    '0.9.0'),
  ('skywatch', 'nftw', '0.9.0', 'sensor_app', '0.9.0'),
  ('skywatch', 'nftw', '0.9.0', 'common_lib', '0.9.0'),
  ('skywatch', 'nftw', '0.9.0', 'system_repo', '0.9.0');

INSERT INTO platform_current_atm_version (project_name, platform_name, atm_version) VALUES
  ('skywatch', 'nftw', '1.0.0');

INSERT INTO csu_csms_relation (csu_name, csc_name, csci_name, css_name, csms_name, csu_description) VALUES
  ('nav_app',    'Navigation',       'Flight Management', 'Air Traffic Control Software', 'Air Traffic Control System', 'Navigation application'),
  ('sensor_app', 'Sensing',          'Surveillance',       'Air Traffic Control Software', 'Air Traffic Control System', 'Sensor data application'),
  ('common_lib', 'Shared Utilities', 'Common Services',    'Air Traffic Control Software', 'Air Traffic Control System', 'Common shared library');
