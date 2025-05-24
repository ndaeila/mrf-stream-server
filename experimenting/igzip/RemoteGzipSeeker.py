import requests
import zlib
import os
import json

class RemoteGzipSeeker:
    def __init__(self, url, index_file="gzip_index.json", chunk_size=65536):
        self.url = url
        self.index_file = index_file
        self.chunk_size = chunk_size
        self.index = self._load_index()
        self.session = requests.Session()

    def _load_index(self):
        if os.path.exists(self.index_file):
            with open(self.index_file, "r") as f:
                return json.load(f)
        return {}

    def _save_index(self):
        with open(self.index_file, "w") as f:
            json.dump(self.index, f)

    def _range_request(self, start, end):
        headers = {"Range": f"bytes={start}-{end}"}
        response = self.session.get(self.url, headers=headers)
        if response.status_code in [200, 206]:
            return response.content
        raise Exception(f"Range request failed: {response.status_code}")

    def _decompress_chunk(self, compressed_bytes):
        d = zlib.decompressobj(16 + zlib.MAX_WBITS)
        return d.decompress(compressed_bytes)

    def seek_and_read(self, uncompressed_offset, n_bytes=1024):
        # Find closest known offset
        known_offsets = sorted(map(int, self.index.keys()))
        closest_offset = max([o for o in known_offsets if o <= uncompressed_offset], default=0)
        compressed_start = self.index.get(str(closest_offset), 0)

        # Start reading chunks from compressed_start
        uncompressed_data = b""
        current_offset = closest_offset
        pos = compressed_start

        while current_offset < uncompressed_offset + n_bytes:
            chunk = self._range_request(pos, pos + self.chunk_size - 1)
            decompressed = self._decompress_chunk(chunk)

            self.index[str(current_offset)] = pos
            self._save_index()

            uncompressed_data += decompressed
            current_offset += len(decompressed)
            pos += self.chunk_size

            if len(chunk) < self.chunk_size:
                break  # EOF

        relative_start = uncompressed_offset - closest_offset
        return uncompressed_data[relative_start:relative_start + n_bytes]



url = "https://lifewise.sapphiremrfhub.com/tocs/202505/2025-05-01_lifewise-health-plan-of-washington_index.json"
seeker = RemoteGzipSeeker(url)

# Read 500 bytes starting at uncompressed offset 100_000
data = seeker.seek_and_read(100_000, 500)
print(data.decode("utf-8", errors="ignore"))