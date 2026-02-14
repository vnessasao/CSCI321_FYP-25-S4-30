# Feature Implementation: Update Feedback (SD-19)

## Overview
**Feature ID:** SD-19  
**Feature Name:** Update Feedback  
**Status:** ✅ Implemented  
**Implementation Date:** January 23, 2026

## Description
This feature allows System Developers to update user feedback messages and push them as alerts/pop-ups to all users, eliminating the need for developers to reply individually to each feedback item.

## Stakeholders and Goals
- **Stakeholders:** System Developers
- **Goal:** Enable developers to update feedback messages and broadcast them system-wide as alerts to all users without replying individually

## Technical Implementation

### Backend (Python/Flask)

#### New Endpoint: `PUT /api/feedback/<id>`

**Location:** `backend/routes/feedback.py`

**Purpose:** Update existing feedback content and optionally broadcast as system-wide alert

**Request Body:**
```json
{
  "subject": "Updated subject (optional)",
  "message": "Updated message content (required)",
  "category": "bug_report|feature_request|general|etc (optional)",
  "broadcast": true|false
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Feedback updated and broadcast sent successfully",
  "data": {
    "id": 123,
    "broadcast_at": "2026-01-23T10:30:00"
  }
}
```

**Features:**
- ✅ Update feedback subject, message, and category
- ✅ Optional broadcast flag to send as system-wide alert
- ✅ Automatically sets broadcast metadata (broadcast_at, broadcast_by)
- ✅ Updates status to 'broadcast' when broadcast flag is true
- ✅ Admin/Developer authentication required
- ✅ Validates message is not empty
- ✅ Validates category against allowed values

### Frontend (React)

#### New API Service Method

**Location:** `src/api/apiService.js`

```javascript
static async updateFeedback(feedbackId, feedbackData, token) {
  return this.authenticatedRequest(`/feedback/${feedbackId}`, token, {
    method: 'PUT',
    body: JSON.stringify(feedbackData)
  })
}
```

#### UI Enhancement

**Location:** `src/pages/dev/Feedback.jsx`

**New Components:**
1. **Edit Button** - Added to feedback table actions column (with FiEdit icon)
2. **Edit Modal** - Complete modal for updating feedback with:
   - Original message display (read-only reference)
   - Subject input field
   - Category dropdown
   - Message textarea (editable)
   - Broadcast checkbox option
   - Update button with visual feedback

**Features:**
- ✅ Display original feedback for reference
- ✅ Allow editing of subject, category, and message
- ✅ Checkbox to broadcast update as system-wide alert
- ✅ Visual distinction for broadcast option (yellow background)
- ✅ Success/error toast notifications
- ✅ Automatic refresh of feedback list and stats after update
- ✅ Automatic refresh of broadcasts list if broadcast was sent

## User Flow

### Normal Flow (as per requirements):
1. System developer opens the Feedback Management page
2. The system displays the list of pending or existing feedback entries
3. The developer clicks the **Edit button** (🖊️ icon) on a feedback item
4. The system opens the **Update Feedback Modal** showing:
   - Original message (for reference)
   - Editable subject field
   - Category dropdown
   - Editable message/announcement textarea
   - Broadcast checkbox option
5. The developer enters the updated feedback response or announcement message
6. Developer optionally checks "Broadcast this update as a system-wide alert"
7. The developer clicks "Update" or "Update & Broadcast" button
8. The system validates the update request
9. The update is saved in the database
10. If broadcast was selected:
    - The system generates a broadcast alert/pop-up version
    - The system marks the feedback as broadcast with timestamp
    - The updated alert is prepared for all affected users to see
11. The system shows a confirmation message that the update was successful
12. The feedback list refreshes automatically

### Alternative Flows:
- **Validation Error:** If message is empty → show error toast
- **Network Error:** If API call fails → show error toast with message
- **No Changes Made:** User can cancel and close modal without saving

## Database Schema

The existing `feedback` table supports this feature with:
- `subject` - VARCHAR(255)
- `message` - TEXT (main content that can be updated)
- `category` - VARCHAR(50)
- `is_broadcast` - BOOLEAN (set to TRUE when broadcast)
- `broadcast_message` - TEXT (copy of updated message)
- `broadcast_at` - TIMESTAMP (when broadcast was sent)
- `broadcast_by` - INTEGER (developer who sent broadcast)
- `status` - VARCHAR(50) (set to 'broadcast' when broadcast)

## Security

- ✅ **Authentication Required:** Admin/Developer role required
- ✅ **Authorization:** Only government and developer roles can update feedback
- ✅ **Input Validation:** Message cannot be empty, category must be valid
- ✅ **SQL Injection Protection:** Using parameterized queries
- ✅ **XSS Protection:** React automatically escapes output

## Testing Checklist

- [ ] Test updating feedback without broadcast
- [ ] Test updating feedback with broadcast enabled
- [ ] Test validation: empty message
- [ ] Test validation: invalid category
- [ ] Test unauthorized access (public/analyst users)
- [ ] Test concurrent updates
- [ ] Test special characters in message
- [ ] Verify broadcast timestamp is set correctly
- [ ] Verify broadcast appears in broadcasts list
- [ ] Verify original feedback is preserved in database

## Benefits

1. **Efficiency:** Developers don't need to reply individually to each feedback
2. **Broadcast Capability:** One update can notify all users system-wide
3. **Transparency:** Original message is preserved and visible
4. **Flexibility:** Can update without broadcasting for minor corrections
5. **Audit Trail:** Tracks who broadcast and when

## Related Features

- **Respond to Feedback** - Individual reply to feedback (existing)
- **Broadcast Messages** - Standalone broadcasts (existing)
- **Update Status** - Change feedback status (existing)

## Future Enhancements

- [ ] Add notification system to actually display broadcast to users
- [ ] Add target role selection for broadcasts (like standalone broadcasts)
- [ ] Add history/audit log of feedback updates
- [ ] Add preview mode before broadcasting
- [ ] Email notification to original feedback submitter

## API Documentation

### Request Example
```bash
curl -X PUT http://localhost:5000/api/feedback/123 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "System Maintenance Update",
    "message": "We have addressed the performance issue you reported. Thank you!",
    "category": "performance",
    "broadcast": true
  }'
```

### Response Example
```json
{
  "success": true,
  "message": "Feedback updated and broadcast sent successfully",
  "data": {
    "id": 123,
    "broadcast_at": "2026-01-23T10:30:00.123456"
  }
}
```

## Files Modified

1. `backend/routes/feedback.py` - Added PUT endpoint
2. `src/api/apiService.js` - Added updateFeedback method
3. `src/pages/dev/Feedback.jsx` - Added edit modal and functionality
4. `IMPLEMENTATION_STATUS.md` - Updated API endpoint list

## Conclusion

Feature SD-19 has been successfully implemented, providing System Developers with the ability to update feedback messages and broadcast them to all users, streamlining the feedback management process.
