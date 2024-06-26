module.exports = {
  apps : [{
    name: 'download_files',
    script: './scripts/download_files.sh',
    cron_restart: '*/5 * * * *',
    exec_mode: 'fork',
    autorestart: false
  },{
    name: 'insert_update_sql',
    script: './scripts/insert_update_sql.sh',
    cron_restart: '*/5 * * * *',
    exec_mode: 'fork',
    autorestart: false
  },
  {
    name: 'insert_update_sql_single_run',
    script: './scripts/insert_update_sql.sh',
    exec_mode: 'fork',
    autorestart: false
  },{
    name: 'update_full_files',
    script: './scripts/update_full_files.sh',
    cron_restart: '0 0 */7 * *',
    exec_mode: 'fork',
    autorestart: false
  }]
};
