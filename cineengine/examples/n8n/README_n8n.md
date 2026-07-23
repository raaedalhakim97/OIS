# Observer World — n8n uploader

A ready-to-import n8n workflow that receives a rendered episode from Claude and
lands it in your storage/pipeline (Google Drive by default), bypassing the 30 MiB
chat upload limit so you get the **full-quality master**.

## Import
1. In n8n: **Workflows → Import from File** → choose `observer_uploader.n8n.json`.
2. Open **Upload to Google Drive** → attach your Google Drive credential and pick a
   target **folder** (e.g. `Observer World / masters`).
3. Click **Active** (top-right). Open the **Webhook** node and copy the
   **Production URL** (`https://<your-n8n>/webhook/observer-upload`).
4. Send that URL back to Claude.

## Flow
```
Webhook (POST, multipart/form-data)
   → Metadata (chapter, episode, title, land, caption, filename)
   → Upload to Google Drive (binary field: file)
   → Respond OK (returns { ok, fileId, name, link })
```

## What Claude posts
`multipart/form-data` with:

| field | example |
|---|---|
| `file` | the `.mp4` (binary) |
| `chapter` | `I` |
| `episode` | `2` |
| `title` | `The Conversation` |
| `land` | `the Home Fields` |
| `caption` | the episode description |
| `filename` | `ch1_ep2_the_conversation.mp4` |

## Auth (recommended)
On the **Webhook** node set **Authentication → Header Auth**, create a header credential
(e.g. `X-Observer-Key: <secret>`), and give Claude the header name + value.

## Test it
```bash
curl -X POST "https://<your-n8n>/webhook/observer-upload" \
  -H "X-Observer-Key: <secret>" \
  -F "file=@ch1_ep2_the_conversation.mp4;type=video/mp4" \
  -F "chapter=I" -F "episode=2" -F "title=The Conversation" \
  -F "land=the Home Fields" -F "caption=..." \
  -F "filename=ch1_ep2_the_conversation.mp4"
```

## Auto-publish (optional)
Insert a node **after Metadata**, reading the binary property `file`:
- **YouTube** → `YouTube: Upload` (native node); map `title` + `caption`.
- **TikTok / Instagram** → **HTTP Request** node to their Content Posting API (or a
  community node).

Keep **Respond OK** last so Claude receives a confirmation + link.

> Binary field name: n8n stores the uploaded file under a property named after the form
> field (`file`). If your version uses `data`, change **inputDataFieldName** on the Drive
> node to `data`.
