import os

import zstandard as zstd

from loggingLocal import log_print


class ZSTDecoder:
    def zst_to_dem(self, input_path):
        try:
            output_path = input_path.replace(".zst","")
            if not os.path.exists(output_path):
                """Распаковка ZST архива"""
                with open(input_path, 'rb') as compressed:
                    dctx = zstd.ZstdDecompressor()
                    with open(output_path, 'wb') as destination:
                        dctx.copy_stream(compressed, destination)
            return output_path
        except Exception as e:
            log_print(f"ERROR converter {e}")
            return None


