# Registration Fix - TODO

## Steps

- [x] Create plan and get approval
- [x] **Step 1**: Update `UserRole` enum in `backend/app/domain/entities/user.py` - changed values to uppercase
- [x] **Step 2**: Update `UserRoleEnum` in `backend/app/infrastructure/database/models/user_model.py` - changed values to uppercase
- [x] **Step 3**: Update `require_admin` check in `backend/app/api/v1/dependencies.py` - changed `"admin"` to `"ADMIN"`
- [x] **Step 4**: Restart Docker containers to apply changes

