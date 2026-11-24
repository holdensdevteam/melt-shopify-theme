import csv, re, sys
from urllib.parse import urlparse, unquote
rows = list(csv.DictReader(open('themeltco_20_nov_2026_pages_202.csv')))
articles = set(open('shopify-articles.txt').read().split())

FRAGS = {  # old slug -> new fragrance handle stem
 'angel':'angel','aubergine':'aubergine','autumn':'autumn','blush':'blush','burgundy':'burgundy','cashmere':'cashmere',
 'christmas':'christmas','dark-wood':'dark-wood','eden':'eden','forest':'forest','love':'love','more':'more',
 'neroli-and-rose-geranium':'neroli-rose-geranium','nocturne':'nocturne','noel':'noel','noir':'noir',
 'nutmeg-and-vetiver':'nutmeg-vetiver','saddle':'saddle','shine':'shine','still':'still',
 'verbena-and-clary-sage':'verbena-clary-sage','violet-and-black-pepper':'violet-black-pepper','white':'white','wisteria':'wisteria'}
RETIRED = {'lily-of-the-valley','carnation','rich-cream','hush','dance','recherche','joy','hyacinth'}
CANDLE_CATS = {
 'autumn-scented-candles':'autumn-collection','spring-scented-candles':'spring-collection','summer-scented-candles':'summer',
 'winter-scented-candles':'winter-collection','christmas-scented-candles':'christmas-collection',
 'mothers-day-scented-candles':'mothers-day','valentines-day-scented-candles':'valentines-day',
 'new-home-scented-candles':'new-home','anniversay-scented-candles':'anniversary','luxury-wedding-candles':'wedding',
 'soft-scented-candles':'soft','warm-scented-candles':'warm','spicy-scented-candles':'spicy','fresh-scented-candles':'fresh',
 'floral-scented-candles':'floral','woody-scented-candles':'woody',
 'feminine-scented-candles':'for-her','masculine-scented-candles':'for-him'}
BEAUTY = {'skincare','body','perfumery','organic-makeup','inika','bath-and-body','beauty'}
PAGES = {
 'our-story':('/pages/our-story',''),'terms-and-conditions':('/policies/terms-of-service',''),
 'privacy-policy':('/policies/privacy-policy',''),
 'cookies-policy':('/policies/privacy-policy','No cookie policy page on Shopify; sent to the privacy policy'),
 'white-label-candles-reed-diffusers':('/pages/white-label',''),'gift-vouchers':('/products/gift-voucher',''),
 'the-chandlers':('/pages/the-chandlers',''),'our-shop-on-the-farm':('/pages/the-shop-on-the-farm',''),
 'becoming-a-melt-stockist':('/pages/become-a-stockist',''),'contact':('/pages/contact',''),
 'delivery':('/pages/delivery-returns',''),'candle-sizes':('/pages/candle-sizes',''),
 'wick-management':('/pages/candle-care','Closest match; no wick page on Shopify'),
 'get-inspired':('/blogs/blog','Closest match; no inspiration page on Shopify'),
 'basket':('/cart',''),
 'gallery':('/','No gallery on Shopify'),'site-map':('/','No HTML sitemap on Shopify'),
 'wishlist':('/','No wishlist on Shopify'),'communication-preferences':('/','No equivalent page on Shopify'),
 'gift-wrapping':('/','Gift wrapping not on Shopify yet'),
}
INGREDIENT_POSTS = {'amber':'ingredient-focus-amber','nutmeg':'nutmeg-everything-you-need-to-know','lavender':'scent-scents-lavender'}
HOME_FLAG = '/'

def junk(r, u, p):
    if u.query: return 'Query-string URL'
    if r['HTTP status code'] in ('403',): return 'Preview link'
    if re.search(r'/page/1/?$', p): return 'Pagination page 1 (already redirected on old site)'
    if p.startswith('/cdn-cgi/') or p == '/robots.txt': return 'System file'
    if ']' in p or 'https:/' in p: return 'Malformed URL'
    if p == '/': return 'Homepage (domain rule covers it)'
    if p == '/products/': return 'Shopify already serves /products, so a redirect would never fire'
    return None

def strip_page(parts):
    if len(parts) >= 2 and parts[-2] == 'page' and parts[-1].isdigit(): return parts[:-2]
    return parts

def dest(p):
    parts = strip_page([x for x in p.strip('/').split('/') if x])
    s = parts[0].lower(); rest = parts[1:]
    leaf = rest[-1].lower() if rest else ''
    if s in BEAUTY: return '/', 'Beauty (discontinued)', ''
    if s == 'blog':
        if not rest: return '/blogs/blog', 'Blog', ''
        if rest[0] == 'category': return '/blogs/blog', 'Blog', 'Blog category; Shopify blog has no categories'
        slug = unquote(rest[0])
        if rest[0] in articles: return '/blogs/blog/' + rest[0], 'Blog', ''
        return '/blogs/blog', 'Blog', 'Post not moved to Shopify; sent to the blog'
    if s == 'scented-candles':
        if not rest: return '/collections/scented-candles', 'Candles', ''
        if leaf in FRAGS: return f'/collections/{FRAGS[leaf]}-fragrance', 'Candles', ''
        if leaf in CANDLE_CATS:
            note = 'Collection has only 1 product right now' if CANDLE_CATS[leaf] in ('for-her','for-him') else ''
            return f'/collections/{CANDLE_CATS[leaf]}', 'Candles', note
        if leaf == 'sample-selection': return '/products/wax-sample-selection', 'Candles', ''
        if leaf == 'gift-voucher': return '/products/gift-voucher', 'Candles', ''
        if leaf in RETIRED: return '/collections/scented-candles', 'Candles', 'Discontinued fragrance; sent to all scented candles'
    if s == 'reed-diffusers':
        if not rest: return '/collections/reed-diffusers', 'Reed diffusers', ''
        stem = re.sub(r'-(scented-)?reed-diffuser.*$', '', leaf)
        if stem in FRAGS: return f'/products/{FRAGS[stem]}-reed-diffuser', 'Reed diffusers', ''
        return '/collections/reed-diffusers', 'Reed diffusers', 'Discontinued fragrance; sent to all reed diffusers'
    if s == 'products':
        if leaf == 'sample-selection': return '/products/wax-sample-selection', 'Shop', ''
        return '/collections/all', 'Shop', ''
    if s == 'hampers' or (s == 'its-on-offer' and 'hamper' in leaf):
        if 'pamper' in leaf: return '/', 'Hampers', 'Pamper hamper was beauty products'
        if leaf == 'taster-box': return '/products/wax-sample-selection', 'Hampers', 'Taster box was a sample selection; closest match'
        return '/collections/hampers-gift-sets', 'Hampers', 'No hampers on Shopify yet; Hampers & Gift Sets has 1 product'
    if s == 'its-on-offer':
        if leaf == 'taster-box': return '/products/wax-sample-selection', 'Offers', 'Taster box was a sample selection; closest match'
        if 'eden' in leaf: return '/collections/eden-fragrance', 'Offers', 'Limited edition no longer sold; sent to Eden'
        if 'travel-tins' in leaf: return '/collections/travel-tin', 'Offers', 'Offer no longer running; sent to travel tins'
        if 'rich-cream' in leaf or 'phoenix' in leaf: return '/collections/scented-candles', 'Offers', 'Discontinued; sent to all scented candles'
        return '/', 'Offers', 'No offers page on Shopify'
    if s in ('candle-holders', 'holders-accessories'):
        return '/', 'Holders & accessories', 'No holders or burners on Shopify (Wax Melt Burners collection is empty)'
    if s == 'ingredient-focus':
        if leaf in INGREDIENT_POSTS: return '/blogs/blog/' + INGREDIENT_POSTS[leaf], 'Ingredients', 'Closest blog post'
        return '/', 'Ingredients', 'No ingredients pages on Shopify'
    if s == 'uncategorised':
        if leaf == 'limited-edition-luxury-glass-jars': return '/collections/glass-jars', 'Other', 'Limited edition no longer sold; sent to glass jars'
        if not rest: return '/', 'Other', 'Old WordPress archive page'
        return '/', 'Beauty (discontinued)', ''
    if s == 'gift-wrapping': return '/', 'Other', 'Gift wrapping not on Shopify yet'
    if s in PAGES and not rest: d, n = PAGES[s]; return d, 'Info pages', n
    return '/', 'Unknown', 'Not sure where this belongs'

review, imp, excluded, seen = [], [], [], {}
for r in rows:
    u = urlparse(r['URL']); p = u.path
    why = junk(r, u, p)
    if why: excluded.append((r['URL'], why)); continue
    d, group, note = dest(p)
    key = p.lower()
    if key in seen:
        excluded.append((r['URL'], 'Duplicate of ' + seen[key])); continue
    seen[key] = p
    if d.rstrip('/') == p.rstrip('/'):
        excluded.append((r['URL'], 'Same path on Shopify')); continue
    review.append(dict(group=group, old=r['URL'], frm=p, to=d, check=note, traffic=int(r['Organic traffic'] or 0), status=r['HTTP status code'], title=r['Title']))

order = ['Candles','Reed diffusers','Shop','Hampers','Offers','Info pages','Blog','Ingredients','Holders & accessories','Other','Beauty (discontinued)','Unknown']
review.sort(key=lambda x: (order.index(x['group']), x['check']=='', -x['traffic'], x['frm']))
out = sys.argv[1]
with open(out + '/melt-redirect-map-review.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['Section','Old URL','Redirect from','Redirect to','Please check','Organic traffic','Old status','Old page title'])
    for x in review: w.writerow([x['group'],x['old'],x['frm'],x['to'],x['check'],x['traffic'],x['status'],x['title']])
with open(out + '/melt-redirects-shopify-import.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['Redirect from','Redirect to'])
    for x in review: w.writerow([x['frm'], x['to']])
with open(out + '/melt-redirects-excluded.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(['Old URL','Why it was left out']); w.writerows(excluded)

import collections as C
print('mapped', len(review), 'excluded', len(excluded))
print(C.Counter(x['group'] for x in review))
print('flagged', sum(1 for x in review if x['check']))
print('flag reasons', C.Counter(x['check'] for x in review if x['check']).most_common())
print('to homepage', sum(1 for x in review if x['to']=='/'), '(beauty', sum(1 for x in review if x['to']=='/' and x['group']=='Beauty (discontinued)'),')')
print('unknown:', [x['frm'] for x in review if x['group']=='Unknown'])
print('distinct destinations', len(set(x['to'] for x in review)))
