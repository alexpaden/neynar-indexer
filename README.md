# Data Sync System

This system utilizes a combination of a Digital Ocean VPS and a managed PostgreSQL database. You can also run the PostgreSQL database directly inside the VPS or manage it externally. Python packages are installed via a shell script with options for environment configuration.

## Requirements

- Digital Ocean VPS (Ubuntu OS recommended)
- Managed PostgreSQL database or local setup
- Python environment with required packages installed via shell script
- AWS S3 for file storage and management

## Initial System Setup

1. Before deploying the application, run the `neynar_indexer_droplet_setup.sh` script to install necessary dependencies on your VPS:

```sh
chmod +x ./neynar_indexer_droplet_setup.sh

./neynar_indexer_droplet_setup.sh
```

2. **Database Configuration:**
   - Set up the PostgreSQL database on Digital Ocean or locally.
   - Use the provided SQL scripts to configure and prepare the database schema.

## Running the Processes

### Manually

1. **Download Script:**
   - Execute the `download_files.sh` script manually to initiate the download process.
   - Start the script with PM2 to automate the download every 5 minutes.

2. **Database Insert/Update:**
   - Run `insert_or_update_sql.py` manually to populate the database initially (this may take a few hours).
   - It's safest to run a single instance initially to avoid conflicts. Multiple is possible

3. **Continuous Sync:**
   - Start the `insert_update_sql` PM2 job, which triggers every 5 minutes to keep the database synchronized within a 10-minute window.

### Automatically

- Use PM2 to manage the application processes:
  - **Download Files:** Automated to run every 5 minutes.
  - **Database Updates:** Automated to run every 5 minutes.
  - **Full File Updates:** Scheduled to clear storage and download new full files once per week.

```sh
pm2 start ecosystem.config.js
