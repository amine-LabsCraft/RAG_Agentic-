-- Do not grant administrative privileges to a predictable demonstration account.
-- Administrators must be assigned explicitly after account creation.
UPDATE public.user_profiles
SET is_admin = false
WHERE user_id IN (
    SELECT id
    FROM auth.users
    WHERE email = 'test@test.com'
);
