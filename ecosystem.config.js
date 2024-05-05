module.exports = {
  apps : [{
    name: 'download_files',
    script: 'python3',
    args: 'download_or_update_files.py',
    cron_restart: '*/5 * * * *',
    exec_mode: 'fork'
  },{
    name: 'insert_update_sql',
    script: 'python3',
    args: 'insert_or_update_sql.py',
    cron_restart: '*/5 * * * *',
    exec_mode: 'fork',
    delay: 45000 // delay in milliseconds
  }]
};
