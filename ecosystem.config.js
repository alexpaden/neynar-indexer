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
  },{
    name: 'update_full_files',
    script: './scripts/update_full_files.sh',  // Updated to call the new Bash script
    cron_restart: '0 0 */7 * *',  // Set this to your desired schedule
    exec_mode: 'fork',
    autorestart: false
  }]
};
