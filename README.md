# Frontend Mentor - Stats preview card component solution

This will help look at 3 data sets and manipulate it with providing me with the full user_id (name)

## This was the notes I had for what I was going to do.

- Pull Integration & User Reads from Platform Analytics page - admin console
- Download Paid users- admin console
- Bring into a GDB as DB tables
- Summary Statistics
  - User Reads
    - Cases
      - App ID
      - User ID
    - NOTE
      - This table also includes time, action, and user agent if we ever want/need to do other analysis that includes. I currently don’t include for simplicity/speed
  - Integration Reads
    - Cases
      - Pipeline ID
      -	User ID
      -	App ID
    -	Note
      -	This table also includes user agent, channel, type, action, timestamp if we ever want/need to do other analysis that includes. I currently don’t include for simplicity/speed
-	Merge user & integration Reads
-	Calc where pipeline ID = 'N/A' to NULL
-	Bring full 'user id' from paid user accounts table to summary reads table
  -	Add User ID String/text field to Reads Sum Table
  -	Add User ID  Trim Field to UserAccounts
  -	Field Calc User ID Trim in the Accounts table to !USER_ID![:8]
  -	Add User ID TEMP to Readsum table & calc over the numeric User ID
  -	Join ReadSum table to account user table by the TEMP & The trim fields
  -	Field Calc the TRUE user ID field into the 'NEW/FULL user ID field in the Read Sum table
-	Add Annualized API Usage
-	  (FREQUENCY/90) * 365
-	Select where App ID is 'N/A' and update to NULL
-	Use Table to Excel tool
-	Open exel file and save as .xlsx
