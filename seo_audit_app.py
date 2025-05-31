from flask import Flask, request, render_template
import requests
from bs4 import BeautifulSoup
import socket
import dns.resolver
from urllib.parse import urlparse

app = Flask(__name__)

# Helper: DNS check
def check_dns_records(domain):
    dns_report = []
    record_types = ['A', 'AAAA', 'MX', 'CNAME', 'NS', 'TXT']
    for rtype in record_types:
        try:
            answers = dns.resolver.resolve(domain, rtype)
            dns_report.append(f"✅ {rtype} record(s) found for {domain}:")
            for answer in answers:
                dns_report.append(f"   - {answer.to_text()}")
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            dns_report.append(f"❌ No {rtype} record found for {domain}.")
        except Exception as e:
            dns_report.append(f"⚠️ Error checking {rtype} record for {domain}: {e}")
    return dns_report

# SEO Audit function
def perform_seo_audit(url):
    report = []
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, 'lxml')

        # Title tag
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.text.strip()
            if 50 <= len(title_text) <= 60:
                report.append(f"✅ Title tag present: '{title_text}' (length: {len(title_text)})")
            else:
                report.append("⚠️ Title tag length issue:")
                report.append(f"   - Title: '{title_text}' (length: {len(title_text)})")
                report.append("   - Recommended 50-60 characters for optimal SEO.")
                report.append("   - Solution: Adjust title to be unique, relevant, and include main keywords naturally.")
        else:
            report.append("❌ No title tag found.")
            report.append("   - Solution: Add a unique and descriptive title tag for each page including target keywords.")

        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            meta_content = meta_desc['content'].strip()
            if 150 <= len(meta_content) <= 160:
                report.append(f"✅ Meta description found: '{meta_content}'")
            else:
                report.append("⚠️ Meta description length issue:")
                report.append(f"   - Description: '{meta_content}' (length: {len(meta_content)})")
                report.append("   - Recommended to keep between 150-160 characters.")
                report.append("   - Solution: Write a unique meta description summarizing page content and include main keywords.")
        else:
            report.append("❌ No meta description found.")
            report.append("   - Solution: Add unique meta descriptions to improve click-through rates and indexing.")

        # H1 tags
        h1_tags = soup.find_all('h1')
        if h1_tags:
            report.append(f"✅ Found {len(h1_tags)} H1 tag(s):")
            for idx, tag in enumerate(h1_tags, 1):
                report.append(f"   - H1 #{idx}: {tag.text.strip()}")
            if len(h1_tags) > 1:
                report.append("⚠️ More than one H1 tag found.")
                report.append("   - SEO best practice recommends only one H1 tag per page.")
        else:
            report.append("❌ No H1 tags found.")
            report.append("   - Solution: Include one H1 tag per page to describe the main content topic.")

        # H2 and H3 tags
        h2_tags = soup.find_all('h2')
        h3_tags = soup.find_all('h3')
        if h2_tags:
            report.append(f"✅ Found {len(h2_tags)} H2 tag(s).")
        if h3_tags:
            report.append(f"✅ Found {len(h3_tags)} H3 tag(s).")

        # URL structure
        parsed_url = urlparse(url)
        if parsed_url.path:
            if '-' in parsed_url.path or parsed_url.path == '/':
                report.append("✅ URL structure looks clean using hyphens or root path.")
            else:
                report.append("⚠️ URL structure check:")
                report.append(f"   - URL path: {parsed_url.path}")
                report.append("   - Recommendation: Use hyphens (-) instead of underscores (_) for readability and SEO.")

        # Content quality
        content = soup.get_text(separator=' ', strip=True)
        word_count = len(content.split())
        if word_count < 500:
            report.append(f"⚠️ Content length issue: Only {word_count} words found.")
            report.append("   - Recommendation: Aim for 500+ words to provide comprehensive content.")
        else:
            report.append(f"✅ Content length is sufficient: {word_count} words.")

        # Internal links
        internal_links = [a for a in soup.find_all('a', href=True)
                          if urlparse(a['href']).netloc == parsed_url.netloc or urlparse(a['href']).netloc == '']
        if internal_links:
            report.append(f"✅ Found {len(internal_links)} internal link(s).")
        else:
            report.append("❌ No internal links found.")
            report.append("   - Solution: Add internal links pointing to relevant pages to improve navigation and SEO.")

        # Image alt attributes
        images = soup.find_all('img')
        missing_alt = [img for img in images if not img.get('alt') or not img.get('alt').strip()]
        if missing_alt:
            report.append(f"⚠️ {len(missing_alt)} image(s) missing alt text.")
            report.append("   - Solution: Add descriptive alt text to images to improve accessibility and SEO.")
        else:
            report.append("✅ All images have alt text.")

        # Outbound links
        outbound_links = [a for a in soup.find_all('a', href=True)
                          if urlparse(a['href']).netloc and urlparse(a['href']).netloc != parsed_url.netloc]
        if outbound_links:
            report.append(f"✅ Found {len(outbound_links)} outbound link(s).")
        else:
            report.append("❌ No outbound links found.")
            report.append("   - Consider adding relevant outbound links to authoritative sources.")

        # Links with nofollow
        nofollow_links = [a for a in soup.find_all('a', rel=True) if 'nofollow' in a['rel']]
        report.append(f"✅ Found {len(nofollow_links)} nofollow link(s).")

        # DNS records check
        domain = parsed_url.netloc
        dns_report = check_dns_records(domain)
        report.append("\n🔧 DNS Records Check:")
        report.extend(dns_report)

        report.append("\n--- SEO Audit Complete ---")

    except requests.RequestException as e:
        report.append(f"❌ Error fetching URL: {e}")
    except Exception as e:
        report.append(f"⚠️ Unexpected error: {e}")

    return report

# Routes
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        report = perform_seo_audit(url)
        return render_template('index.html', report=report, url=url)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
