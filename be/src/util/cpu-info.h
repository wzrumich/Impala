// Copyright 2012 Cloudera Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.


#ifndef IMPALA_UTIL_CPU_INFO_H
#define IMPALA_UTIL_CPU_INFO_H

#include <string>
#include <boost/cstdint.hpp>

#include "common/logging.h"

namespace impala {

// CpuInfo is an interface to query for cpu information at runtime.  The caller can
// ask for the sizes of the caches and what hardware features are supported.
// On Linux, this information is pulled from a couple of sys files (/proc/cpuinfo and 
// /sys/devices)
class CpuInfo {
 public:
  static const int64_t SSE3    = (1 << 1);
  static const int64_t SSE4_1  = (1 << 2);
  static const int64_t SSE4_2  = (1 << 3);

  // Cache enums for L1 (data), L2 and L3 
  enum CacheLevel {
    L1_CACHE = 0,
    L2_CACHE = 1,
    L3_CACHE = 2,
  };

  // Initialize CpuInfo.
  static void Init();

  // Returns all the flags for this cpu
  static int64_t hardware_flags() {
    DCHECK(initialized_);
    return hardware_flags_;
  }
  
  // Returns whether of not the cpu supports this flag
  inline static bool IsSupported(long flag) {
    DCHECK(initialized_);
    return (hardware_flags_ & flag) != 0;
  }

  // Toggle a hardware feature on and off.  It is not valid to turn on a feature
  // that the underlying hardware cannot support. This is useful for testing.
  static void EnableFeature(long flag, bool enable);

  // Returns the size of the cache in KB at this cache level
  static long CacheSize(CacheLevel level) {
    DCHECK(initialized_);
    return cache_sizes_[level];
  }

  // Returns the number of cpu cycles per millisecond
  static int64_t cycles_per_ms() {
    DCHECK(initialized_);
    return cycles_per_ms_;
  }

  // Returns the number of cores (including hyper-threaded) on this machine.
  static int num_cores() { 
    DCHECK(initialized_);
    return num_cores_; 
  }

  // Returns the model name of the cpu (e.g. Intel i7-2600)
  static std::string model_name() { 
    DCHECK(initialized_);
    return model_name_;
  }

  static std::string DebugString();

 private:
  static bool initialized_;
  static int64_t hardware_flags_;
  static int64_t original_hardware_flags_;
  static long cache_sizes_[L3_CACHE + 1];
  static int64_t cycles_per_ms_;
  static int num_cores_;
  static std::string model_name_;
};

}
#endif
