# OCR triage of phishing captures

Triaged 65 images; **21** (32.3%) show neither credential vocabulary nor their own domain token and are flagged as unlikely phishing pages.

| Flagged image | Domain token | OCR sample |
|---|---|---|
| phishing_trendndailyinsider_com_01.png | trendndailyinsider | Trend I Daity Insider PayPal GIFT CARD siq 00 Are You Ready to Claim Your Free P |
| phishing_contaboserver_net_01.png | contaboserver | SEUR Enviar Recibir Devolver miSEUR Empresas Puntos Pickup Ayuda Inicia sesion 0 |
| phishing_blogspot_com_01.png | blogspot | 42 1#3Em4 Jm, {Ffacecook-ran blogspoccom JJMZEIA TTJAT#1Z' #Ee1j2810j1jig? 1327T |
| phishing_roblox_rw_01.png | roblox | Charts Marketplace Create Something went wrong 404 Page Not found Back Home |
| phishing_vercel_app_03.png | vercel | amazon Search Amazonin Deliver t0 Guest Update Address Beauty products Explore t |
| phishing_3658995_cc_01.png | 3658995 | bet365 FIFA WORLD CUP UNITED STATES / CANADA / MEXICO 3 6 5 8 #5z86 service Onli |
| phishing_roblox_ly_01.png | roblox | Charts Marketplace Create Robux Search Sign Up 3D FreyaPeler9 Joln Add Connectio |
| phishing_s4w_in_01.png | s4w | Charts Marketplace Create Robux Search Sign Up 3D bubble @ Joln Add Connection @ |
| phishing_momabb_top_01.png | momabb | RECRUTAMENTO DIGITAL Vaga Verificada S Assistente de Atendimento Remoto Selecao  |
| phishing_tokenpoicet_pro_01.png | tokenpoicet | imToken, "#r21l 645002788, #tsaPEI imToken Am   *F   Ibal 25   Et# T# BRtiI] MRt |
| phishing_s4w_in_02.png | s4w | Charts Marketplace Create Robux Search Sign Up 3D BlacknightCHOAD @ Joln Add Con |
| phishing_com_pt_01.png | pt | " Charts Marketplace Create [2] A Crossroads Game_? By OneWhoFinds Favorite Abou |
| phishing_imtokein-cdn_autos_01.png | imtokein | imToken IBQTil R2+0 #MJFL 103 TokenHub 0395 #iLat+FEz EB: #RtaI# Fille - Alljunl |
| phishing_auth-secure_me_01.png | auth | Journey Oops! It seems we are preventing You from accessing this page: If you be |
| phishing_19504jjb_com_01.png | 19504jjb | #BixW 75ik5 @7uu;IB AX} Blit #ataw TEEBB LJA+373 Mniap aieae |
| phishing_6686-vn_net_01.png | 6686 | facebook Search for a brandlproductlsuppliers EAONE Fashlon Dress Belts S16.50 / |
| phishing_cfolks_pl_01.png | cfolks | wxcvb Sample Page Strona nie zostata znaleziona Strona; ktorej szukasz, nie istn |
| phishing_justns_ru_01.png | justns | Not Found The requested URL was not found on this server Additionally: 404 Not F |
| phishing_co_za_01.png | za | Beyond limits Home Cookie Policy Privacy Policy Terms Of Use |
| phishing_weebly_com_01.png | weebly | Aufgrund kirzlicher Serveranderungen werden einige inaktive Konten dauerhaft gel |
| phishing_imtokein-cdn_xyz_01.png | imtokein | Error 504 IEAJIe: 67.159.48.149 #AIB: 111.92.242.95 @RIAREAf I+AIAH? CDNTRIARERR |

## What this is and is not

- It is a screen for dead campaigns, parked domains, and blank dashboards.
- It is not a label: a real phishing page can omit credential words in OCR,
  and a parked page can contain the domain token.
- Nothing was deleted. Flagged rows keep their label; with `--apply` their
  confidence drops to 0.3 and the reason is recorded.
