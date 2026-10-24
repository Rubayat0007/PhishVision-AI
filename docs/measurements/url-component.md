# P-3: the URL component, measured

n=24 captures that recorded a `source_url` (12 phishing, 12 legitimate).

| Risk threshold | phishing detected without URL | with URL | legit flagged without | with |
|---|---|---|---|---|
| 20/100 | 8/12 | 9/12 | 4/12 | 4/12 |
| 25/100 | 3/12 | 6/12 | 1/12 | 1/12 |
| 30/100 | 2/12 | 3/12 | 1/12 | 1/12 |
| 35/100 | 0/12 | 2/12 | 0/12 | 0/12 |

Mean risk change with URL: overall +1.88, phishing +3.75, legitimate +0.00 points (of 100).

## Reading this

- The URL raises risk mainly for phishing captures and barely for legitimate
  ones, which is the direction the 30% weight assumes.
- The effect is small in absolute terms: a couple of points on a 100-point
  scale, enough to move a borderline case and not enough to rescue a clear miss.
- The URL analysed is the *reported* phishing URL, the most favourable case;
  a redirector or a benign-looking host would score lower.

## Limits

- 12 images per class: one case is 8 percentage points.
- Feed-derived labels; OCR triage flagged ~36% of phishing captures.
- Same images with and without URL, so this isolates the URL component's effect.
