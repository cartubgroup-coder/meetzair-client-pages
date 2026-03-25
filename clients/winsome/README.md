# Winsome — BTT Agent Page

**Agent:** Winsome
**Template base:** BTT Landing Page — Apply & Approve.html
**URL:** winsome.joinbtt.com (once JoinBTT.com domain is live)
**Created:** 2026-03-25

---

## What's Customized

| Section | Change |
|---------|--------|
| Title tag | "Join BTT — via Winsome" |
| Hero eyebrow | "Winsome Invited You — Business Opportunity…" |
| Hero description | References Winsome by name |
| Video section label | "From Winsome" |
| Video section copy | Winsome's personal message framing |
| Video pull quote | "I wouldn't have sent you here if I didn't believe in it." |
| Form payload | `ref_agent: 'Winsome'` + UTM fields |
| Hidden form fields | ref_agent, utm_source, utm_medium, utm_campaign |
| UTM capture JS | Reads URL params → populates hidden fields on load |

Everything else — BTT branding, logo, GHL webhook, A2P compliance, all sections — is identical to the base template.

---

## Swapping in Winsome's Real Video

Replace the `video-player` div in `index.html` with one of these:

**Option A — YouTube/Vimeo embed:**
```html
<div class="video-player fade-in fade-delay-2">
  <iframe
    src="https://www.youtube.com/embed/YOUR_VIDEO_ID?autoplay=0&rel=0"
    width="100%" height="100%"
    frameborder="0"
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
    allowfullscreen
  ></iframe>
</div>
```

**Option B — HeyGen AI clone embed:**
```html
<div class="video-player fade-in fade-delay-2">
  <iframe
    src="YOUR_HEYGEN_SHARE_URL"
    width="100%" height="100%"
    frameborder="0"
    allow="autoplay; fullscreen"
    allowfullscreen
  ></iframe>
</div>
```

**Option C — Self-hosted video file:**
```html
<div class="video-player fade-in fade-delay-2">
  <video controls poster="winsome-poster.jpg" style="width:100%;height:100%;object-fit:cover;border-radius:16px;">
    <source src="winsome-intro.mp4" type="video/mp4">
  </video>
</div>
```

---

## Adding Winsome's Photo

The template doesn't currently show agent photos. If you want to add one:
- Place the photo at: `clients/winsome/winsome-photo.jpg`
- Recommended size: 400×500px, face centered, professional setting
- Add it above the video section or in the form sidebar

---

## Tracking Links

Every link Winsome shares should include tracking params:

```
# Basic link
https://winsome.joinbtt.com

# With source tracking (for Instagram)
https://winsome.joinbtt.com?utm_source=instagram&utm_medium=social&utm_campaign=march-push

# The ref=Winsome param is already hardcoded in the form — no need to add it to links
# But you can include it for clarity:
https://winsome.joinbtt.com?ref=Winsome&utm_source=text&utm_medium=sms
```

The form always sends `ref_agent: Winsome` regardless of URL params. UTM params are optional but useful for tracking which channel drove the lead.

---

## Vercel Deployment

Once JoinBTT.com is registered and the GitHub repo is set up:

1. Create a Vercel project pointing to `clients/winsome/` folder
2. Set custom domain: `winsome.joinbtt.com`
3. In your domain registrar, add a DNS record:
   ```
   Type: CNAME
   Name: winsome
   Value: cname.vercel-dns.com
   ```
4. Vercel will auto-deploy on every push to GitHub

---

## What Leads Look Like in GHL

When Winsome's page gets a submission:
- Contact created in BTT's Recruiting pipeline (Pre-Licensed Prospect stage)
- Custom field `ref_agent` = "Winsome"
- Custom field `utm_source` = wherever they came from
- Marketing Director gets SMS alert: "New BTT applicant: [Name] via Winsome"
- AI agent (Jordan) reviews and logs the decision
