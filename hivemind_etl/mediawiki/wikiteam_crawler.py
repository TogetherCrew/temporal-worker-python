import logging
import os

from wikiteam3.dumpgenerator import DumpGenerator


class WikiteamCrawler:
    def __init__(
        self,
        community_id: str,
        xml: bool = True,
        force: bool = True,
        curonly: bool = True,
        namespaces: list[int] = [],
        proxy_url: str = "",
        **kwargs,
    ) -> None:
        self.community_id = community_id
        self.xml = xml
        self.force = force
        self.curonly = curonly
        self.extra_params = kwargs
        self.namespaces = namespaces
        self.proxy_url = proxy_url

    def crawl(self, api_url: str, dump_path: str) -> None:
        """
        Crawl the mediawiki dump from the given api url and save it to the given path

        Parameters
        ----------
        api_url : str
            The url of the mediawiki api
        dump_path : str
            The path to save the dump file
        """
        # Create a list of parameters analogous to the terminal command:
        params = [
            "--api",
            api_url,
            "--path",
            dump_path,
        ]

        # Add optional parameters based on configuration
        if self.xml:
            params.append("--xml")
        if self.force:
            params.append("--force")
        if self.curonly:
            params.append("--curonly")
        if self.namespaces:
            params.append(f"--namespaces")
            params.append(f"{','.join(map(str, self.namespaces))}")
        if self.proxy_url:
            params.append(f"--proxy")
            params.append(self.proxy_url)

        # Add any extra parameters passed during initialization
        for key, value in self.extra_params.items():
            if isinstance(value, bool):
                if value:
                    params.append(f"--{key}")
            else:
                params.extend([f"--{key}", str(value)])

        logging.info(f"Crawling mediawiki dump from {api_url} to {dump_path}")
        logging.info(f"Parameters: {params}")

        # Directly call the DumpGenerator static __init__ method which will parse these parameters,
        # execute the dump generation process, and run through the rest of the workflow.
        DumpGenerator(params)

    def delete_dump(self, dump_path: str) -> None:
        """
        Delete the dumped file at the specified path.

        Parameters
        ----------
        dump_path : str
            The path to the dump file to be deleted
        """
        try:
            if os.path.exists(dump_path):
                os.remove(dump_path)
                logging.info(f"Successfully deleted dump file at {dump_path}")
            else:
                logging.warning(f"Dump file not found at {dump_path}")
        except Exception as e:
            logging.error(f"Error deleting dump file at {dump_path}: {str(e)}")
            raise
