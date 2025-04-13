import logging
import xml.etree.ElementTree as ET
import os
import glob

from hivemind_etl.mediawiki.schema import Contributor, Page, Revision, SiteInfo


def parse_mediawiki_xml(file_dir: str) -> list[Page]:
    """Parse a MediaWiki XML dump file and extract page information.

    This function processes a MediaWiki XML dump file, extracting detailed information
    about pages, their revisions, and contributors. The data is structured into
    Pydantic models for type safety and validation.

    Parameters
    ----------
    file_dir : str
        Path to the directory containing the MediaWiki XML dump file to be parsed.

    Returns
    -------
    pages : list[Page]
        A list of Page objects containing the parsed data. Each Page object includes:
        - Basic page information (title, namespace, page_id)
        - Revision details (revision_id, timestamp, text, etc.)
        - Contributor information (username, user_id)

    Examples
    --------
    >>> pages = parse_mediawiki_xml("wiki_dump_directory")
    >>> for page in pages:
    ...     print(f"Page: {page.title}")
    ...     if page.revision:
    ...         print(f"Last edited by: {page.revision.contributor.username}")

    Notes
    -----
    - The function handles optional fields gracefully, setting them to None when not present
    - XML namespaces are automatically handled for MediaWiki export format
    - The text content retains XML escapes (e.g., &lt; for <)
    - The function logs the total number of pages processed
    """
    # Find XML file in the directory
    xml_files = glob.glob(os.path.join(file_dir, "*.xml"))
    if not xml_files:
        raise FileNotFoundError(f"No XML files found in directory: {file_dir}")

    # Use the first XML file found
    # there should be only one xml file in the directory (wikiteam3 crawler settings)
    xml_file = xml_files[0]
    logging.info(f"Found XML file: {xml_file}")

    namespaces = {"mw": "http://www.mediawiki.org/xml/export-0.11/"}
    # Parse the XML file
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # --- Extract Site Information ---
    siteinfo_el = root.find("mw:siteinfo", namespaces)
    siteinfo = SiteInfo()
    if siteinfo_el is not None:
        for tag in ["sitename", "dbname", "base", "generator"]:
            el = siteinfo_el.find(f"mw:{tag}", namespaces)
            setattr(siteinfo, tag, el.text if el is not None else None)

    # --- Process Each Page ---
    pages = []
    for page in root.findall("mw:page", namespaces):
        page_data = Page()
        # Extract basic page details: title, namespace, page id
        title_el = page.find("mw:title", namespaces)
        page_data.title = title_el.text if title_el is not None else None

        ns_el = page.find("mw:ns", namespaces)
        page_data.namespace = ns_el.text if ns_el is not None else None

        id_el = page.find("mw:id", namespaces)
        page_data.page_id = id_el.text if id_el is not None else None

        # Extract revision details
        revision = page.find("mw:revision", namespaces)
        if revision is not None:
            rev_data = Revision()
            rev_id_el = revision.find("mw:id", namespaces)
            rev_data.revision_id = rev_id_el.text if rev_id_el is not None else None

            parentid_el = revision.find("mw:parentid", namespaces)
            rev_data.parent_revision_id = (
                parentid_el.text if parentid_el is not None else None
            )

            timestamp_el = revision.find("mw:timestamp", namespaces)
            rev_data.timestamp = timestamp_el.text if timestamp_el is not None else None

            # Revision comment (present only on some pages)
            comment_el = revision.find("mw:comment", namespaces)
            rev_data.comment = comment_el.text if comment_el is not None else ""

            # Contributor information
            contributor = revision.find("mw:contributor", namespaces)
            if contributor is not None:
                cont_data = Contributor()
                username_el = contributor.find("mw:username", namespaces)
                cont_data.username = (
                    username_el.text if username_el is not None else None
                )

                user_id_el = contributor.find("mw:id", namespaces)
                cont_data.user_id = user_id_el.text if user_id_el is not None else None

                rev_data.contributor = cont_data

            # Other revision details like model and format
            model_el = revision.find("mw:model", namespaces)
            rev_data.model = model_el.text if model_el is not None else None

            format_el = revision.find("mw:format", namespaces)
            rev_data.format = format_el.text if format_el is not None else None

            # Extract the full text content; note that XML escapes are retained (e.g., &lt;)
            text_el = revision.find("mw:text", namespaces)
            rev_data.text = text_el.text if text_el is not None else ""

            # Capture sha1 if needed
            sha1_el = revision.find("mw:sha1", namespaces)
            rev_data.sha1 = sha1_el.text if sha1_el is not None else None

            page_data.revision = rev_data

        pages.append(page_data)

    logging.info(f"Total pages processed: {len(pages)}\n")
    return pages
