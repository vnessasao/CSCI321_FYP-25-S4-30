-- Grant super admin privileges to government users
-- This script allows government users to manage user accounts

-- Replace 'government@gmail.com' with the actual email address of the government user
-- who should have super admin privileges

-- UPDATE users
-- SET is_super_admin = TRUE
-- WHERE email = 'admin@trafficsg.gov' AND role = 'government';

select * from users

-- Verify the change


-- Alternative: Grant super admin to all government users
-- Uncomment the lines below if you want to grant super admin to ALL government users
-- UPDATE users SET is_super_admin = TRUE WHERE role = 'government';
-- SELECT id, email, role, is_super_admin FROM users WHERE role = 'government';
