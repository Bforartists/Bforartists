/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#include "BLI_fileops.hh"
#include "BLI_function_ref.hh"
#include "BLI_serialize.hh"

#include "BKE_bake_items.hh"

namespace blender::bke::bake {

/**
 * Reference to a slice of memory typically stored on disk.
 * A blob is a "binary large object".
 */
struct BlobSlice {
  std::string name;
  IndexRange range;

  std::shared_ptr<io::serialize::DictionaryValue> serialize() const;
  static std::optional<BlobSlice> deserialize(const io::serialize::DictionaryValue &io_slice);
};

/**
 * Abstract base class for loading binary data.
 */
class BlobReader {
 public:
  /**
   * Read the data from the given slice into the provided memory buffer.
   * \return True on success, otherwise false.
   */
  [[nodiscard]] virtual bool read(const BlobSlice &slice, void *r_data) const = 0;

  /**
   * Provides an #istream that can be used to read the data from the given slice.
   * \return True on success, otherwise false.
   */
  [[nodiscard]] virtual bool read_as_stream(const BlobSlice &slice,
                                            FunctionRef<bool(std::istream &)> fn) const;
};

/**
 * Abstract base class for writing binary data.
 */
class BlobWriter {
 public:
  /**
   * Write the provided binary data.
   * \return Slice where the data has been written to.
   */
  virtual BlobSlice write(const void *data, int64_t size) = 0;

  /**
   * Provides an #ostream that can be used to write the blob.
   * \param file_extension: May be used if the data is written to an independent file. Based on the
   *   implementation, this may be ignored.
   * \return Slice where the data has been written to.
   */
  virtual BlobSlice write_as_stream(StringRef file_extension,
                                    FunctionRef<void(std::ostream &)> fn);
};

/**
 * Allows deduplicating data before it's written.
 */
class BlobWriteSharing : NonCopyable, NonMovable {
 private:
  struct StoredByRuntimeValue {
    /**
     * Version of the shared data that was written before. This is needed because the data might
     * be changed later without changing the #ImplicitSharingInfo pointer.
     */
    int64_t sharing_info_version;
    /**
     * Identifier of the stored data. This includes information for where the data is stored (a
     * #BlobSlice) and optionally information for how it is loaded (e.g. endian information).
     */
    std::shared_ptr<io::serialize::DictionaryValue> io_data;
  };

  /**
   * Map used to detect when some data has already been written. It keeps a weak reference to
   * #ImplicitSharingInfo, allowing it to check for equality of two arrays just by comparing the
   * sharing info's pointer and version.
   */
  Map<const ImplicitSharingInfo *, StoredByRuntimeValue> stored_by_runtime_;

  struct SliceHash {
    uint64_t a;
    uint64_t b;

    BLI_STRUCT_EQUALITY_OPERATORS_2(SliceHash, a, b)

    uint64_t hash() const
    {
      return get_default_hash(this->a, this->b);
    }
  };

  /**
   * Remembers where data was stored based on the hash of the data. This allows us to skip writing
   * the same array again if it has the same hash.
   */
  Map<SliceHash, BlobSlice> slice_by_content_hash_;

 public:
  ~BlobWriteSharing();

  /**
   * Check if the data referenced by `sharing_info` has been written before. If yes, return the
   * identifier for the previously written data. Otherwise, write the data now and store the
   * identifier for later use.
   * \return Identifier that indicates from where the data has been written.
   */
  [[nodiscard]] std::shared_ptr<io::serialize::DictionaryValue> write_implicitly_shared(
      const ImplicitSharingInfo *sharing_info,
      FunctionRef<std::shared_ptr<io::serialize::DictionaryValue>()> write_fn);

  /**
   * Checks if the given data was written before. If it was, it's not written again, but a
   * reference to the previously written data is returned. If the data is new, it's written now.
   * Its hash is remembered so that the same data won't be written again.
   */
  [[nodiscard]] std::shared_ptr<io::serialize::DictionaryValue> write_deduplicated(
      BlobWriter &writer, const void *data, int64_t size_in_bytes);
};

/**
 * Avoids loading the same data multiple times by caching and sharing previously read buffers.
 */
class BlobReadSharing : NonCopyable, NonMovable {
 private:
  /**
   * Use a mutex so that #read_shared can be implemented in a thread-safe way.
   */
  mutable std::mutex mutex_;
  /**
   * Map used to detect when some data has been previously loaded. This keeps strong
   * references to #ImplicitSharingInfo.
   */
  mutable Map<std::string, ImplicitSharingInfoAndData> runtime_by_stored_;

 public:
  ~BlobReadSharing();

  /**
   * Check if the data identified by `io_data` has been read before or load it now.
   * \return Shared ownership to the read data, or none if there was an error.
   */
  [[nodiscard]] std::optional<ImplicitSharingInfoAndData> read_shared(
      const io::serialize::DictionaryValue &io_data,
      FunctionRef<std::optional<ImplicitSharingInfoAndData>()> read_fn) const;
};

/**
 * A specific #BlobReader that reads from disk.
 */
class DiskBlobReader : public BlobReader {
 private:
  const std::string blobs_dir_;
  mutable std::mutex mutex_;
  mutable Map<std::string, std::unique_ptr<fstream>> open_input_streams_;

 public:
  DiskBlobReader(std::string blobs_dir);
  [[nodiscard]] bool read(const BlobSlice &slice, void *r_data) const override;
};

/**
 * A specific #BlobWriter that writes to a file on disk.
 */
class DiskBlobWriter : public BlobWriter {
 private:
  /** Directory path that contains all blob files. */
  std::string blob_dir_;
  /** Name of the file that data is written to. */
  std::string base_name_;
  std::string blob_name_;
  /** File handle. The file is opened when the first data is written. */
  std::fstream blob_stream_;
  /** Current position in the file. */
  int64_t current_offset_ = 0;
  /** Used to generate file names for bake data that is stored in independent files. */
  int independent_file_count_ = 0;

 public:
  DiskBlobWriter(std::string blob_dir, std::string base_name);

  BlobSlice write(const void *data, int64_t size) override;

  BlobSlice write_as_stream(StringRef file_extension,
                            FunctionRef<void(std::ostream &)> fn) override;
};

void serialize_bake(const BakeState &bake_state,
                    BlobWriter &blob_writer,
                    BlobWriteSharing &blob_sharing,
                    std::ostream &r_stream);

std::optional<BakeState> deserialize_bake(std::istream &stream,
                                          const BlobReader &blob_reader,
                                          const BlobReadSharing &blob_sharing);

}  // namespace blender::bke::bake
