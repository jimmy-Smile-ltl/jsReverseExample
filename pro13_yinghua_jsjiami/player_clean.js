var script = document["createElement"]("script");
((script["src"] = "https://www.maccms.xyz/dmplayer.js"),
  (script["type"] = "text/javascript"),
  (script["async"] = !![]),
  document["head"]["appendChild"](script));
let art;
function showError(_0xbd09b1) {
  const _0x1e3b8b = _0x2b2717,
    _0x39459a = { siWHv: "loading-box" };
  document["getElementById"](_0x39459a["siWHv"])["style"]["display"] = "none";
  const _0x402d27 = document["getElementById"]("artplayer");
  _0x402d27["innerHTML"] =
    '\n        <div style="color: #fff; text-align: center; padding-top: 20%; font-family: sans-serif;">\n            <div style="font-size: 18px;">' +
    _0xbd09b1 +
    "</div>\n        </div>\n    ";
}
!playerConfig["videoUrl"] ? showError("仅供学习与技术交流，禁止商用！") : !window["isUnauthorized"] && init();
async function init() {
  const _0x21b1a4 = _0x2b2717,
    _0x3db60a = {
      IHhVR: function (_0x27f012, _0x2a58c2) {
        return _0x27f012(_0x2a58c2);
      },
      uQdHT: "loading-box",
      egdRK: "none",
      rnWEN: function (_0x448f9c) {
        return _0x448f9c();
      },
      zqpnq: function (_0x3a4f34, _0x3a6d46) {
        return _0x3a4f34 === _0x3a6d46;
      },
      jlSbk: "ZvKJD",
      Ujawv: function (_0x2ad54f, _0x30c339) {
        return _0x2ad54f + _0x30c339;
      },
      OGbHx: "系统错误: ",
    };
  try {
    if (playerConfig["ads"]["pre_roll"]["enabled"])
      ((document["getElementById"](_0x3db60a["uQdHT"])["style"]["display"] = _0x3db60a["egdRK"]),
        document["body"]["classList"]["remove"]("loading"),
        await _0x3db60a["rnWEN"](showPreRoll));
    else {
      if (_0x3db60a["zqpnq"](_0x3db60a["jlSbk"], _0x3db60a["jlSbk"])) {
        const { url: _0x2ca8d6, type: _0x165883 } = await resolveVideo();
        initPlayer(_0x2ca8d6, _0x165883);
      } else return _0x3db60a["IHhVR"](_0x5880b7, "landscape");
    }
  } catch (_0x5de70b) {
    _0x3db60a["IHhVR"](showError, _0x3db60a["Ujawv"](_0x3db60a["OGbHx"], _0x5de70b["message"]));
  }
}
function _0x12d4(_0x2e31b7, _0x642c18) {
  const _0x1a560c = _0x1a56();
  return (
    (_0x12d4 = function (_0x12d40a, _0x39eec7) {
      _0x12d40a = _0x12d40a - 0x112;
      let _0x3b890b = _0x1a560c[_0x12d40a];
      if (_0x12d4["fhmePF"] === undefined) {
        var _0x394ee6 = function (_0x5efeb8) {
          const _0x373da6 = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=";
          let _0x3302c1 = "",
            _0x54d2bd = "";
          for (
            let _0x1d623d = 0x0, _0x16d3d8, _0x25d48a, _0x3e7a0b = 0x0;
            (_0x25d48a = _0x5efeb8["charAt"](_0x3e7a0b++));
            ~_0x25d48a && ((_0x16d3d8 = _0x1d623d % 0x4 ? _0x16d3d8 * 0x40 + _0x25d48a : _0x25d48a), _0x1d623d++ % 0x4)
              ? (_0x3302c1 += String["fromCharCode"](0xff & (_0x16d3d8 >> ((-0x2 * _0x1d623d) & 0x6))))
              : 0x0
          ) {
            _0x25d48a = _0x373da6["indexOf"](_0x25d48a);
          }
          for (let _0x2abcfe = 0x0, _0x22cb10 = _0x3302c1["length"]; _0x2abcfe < _0x22cb10; _0x2abcfe++) {
            _0x54d2bd += "%" + ("00" + _0x3302c1["charCodeAt"](_0x2abcfe)["toString"](0x10))["slice"](-0x2);
          }
          return decodeURIComponent(_0x54d2bd);
        };
        const _0x471327 = function (_0x342d8a, _0x1395a0) {
          let _0x3caa29 = [],
            _0x567e9e = 0x0,
            _0x5389de,
            _0x17776f = "";
          _0x342d8a = _0x394ee6(_0x342d8a);
          let _0x3343dc;
          for (_0x3343dc = 0x0; _0x3343dc < 0x100; _0x3343dc++) {
            _0x3caa29[_0x3343dc] = _0x3343dc;
          }
          for (_0x3343dc = 0x0; _0x3343dc < 0x100; _0x3343dc++) {
            ((_0x567e9e =
              (_0x567e9e + _0x3caa29[_0x3343dc] + _0x1395a0["charCodeAt"](_0x3343dc % _0x1395a0["length"])) % 0x100),
              (_0x5389de = _0x3caa29[_0x3343dc]),
              (_0x3caa29[_0x3343dc] = _0x3caa29[_0x567e9e]),
              (_0x3caa29[_0x567e9e] = _0x5389de));
          }
          ((_0x3343dc = 0x0), (_0x567e9e = 0x0));
          for (let _0x19bc1a = 0x0; _0x19bc1a < _0x342d8a["length"]; _0x19bc1a++) {
            ((_0x3343dc = (_0x3343dc + 0x1) % 0x100),
              (_0x567e9e = (_0x567e9e + _0x3caa29[_0x3343dc]) % 0x100),
              (_0x5389de = _0x3caa29[_0x3343dc]),
              (_0x3caa29[_0x3343dc] = _0x3caa29[_0x567e9e]),
              (_0x3caa29[_0x567e9e] = _0x5389de),
              (_0x17776f += String["fromCharCode"](
                _0x342d8a["charCodeAt"](_0x19bc1a) ^ _0x3caa29[(_0x3caa29[_0x3343dc] + _0x3caa29[_0x567e9e]) % 0x100],
              )));
          }
          return _0x17776f;
        };
        ((_0x12d4["ktvkvv"] = _0x471327), (_0x2e31b7 = arguments), (_0x12d4["fhmePF"] = !![]));
      }
      const _0x3cf8d1 = _0x1a560c[0x0],
        _0x1e9520 = _0x12d40a + _0x3cf8d1,
        _0x525ecf = _0x2e31b7[_0x1e9520];
      return (
        !_0x525ecf
          ? (_0x12d4["kQBSdb"] === undefined && (_0x12d4["kQBSdb"] = !![]),
            (_0x3b890b = _0x12d4["ktvkvv"](_0x3b890b, _0x39eec7)),
            (_0x2e31b7[_0x1e9520] = _0x3b890b))
          : (_0x3b890b = _0x525ecf),
        _0x3b890b
      );
    }),
    _0x12d4(_0x2e31b7, _0x642c18)
  );
}
async function resolveVideo() {
  const _0xff2fd2 = _0x2b2717,
    _0x150847 = {
      OmzTq: "loading-box",
      DgUjd: "none",
      qUgXZ: "loading",
      JNLfN: function (_0x522f03, _0x200767) {
        return _0x522f03(_0x200767);
      },
      bfDAn: "api/resolve.php?token=",
      sCbgD: function (_0xc4b521, _0x4d7608) {
        return _0xc4b521 !== _0x4d7608;
      },
      BpKPS: function (_0x3f15f3, _0x2aa1f1) {
        return _0x3f15f3 !== _0x2aa1f1;
      },
      CkVLa: "xsSzB",
      gSpKG: "无法解析视频。",
      NNdka: function (_0x503b86, _0x544c9b) {
        return _0x503b86 === _0x544c9b;
      },
      sIxVV: "auto",
      IrWmm: ".m3u8",
      HNPRe: ".flv",
      rELHw: ".mp4",
    },
    _0x182214 = await _0x150847["JNLfN"](
      fetch,
      _0x150847["bfDAn"] + _0x150847["JNLfN"](encodeURIComponent, playerConfig["apiToken"]),
    ),
    _0x1a6147 = await _0x182214["json"]();
  if (_0x150847["sCbgD"](_0x1a6147["code"], 0xc8)) {
    if (_0x150847["BpKPS"](_0x150847["CkVLa"], _0x150847["CkVLa"])) {
      const _0x5c9d1a = _0x2d0ed6["getElementById"](_0x150847["OmzTq"]);
      if (_0x5c9d1a) _0x5c9d1a["style"]["display"] = _0x150847["DgUjd"];
      _0x541216["body"]["classList"]["remove"](_0x150847["qUgXZ"]);
    } else throw new Error(_0x1a6147["msg"] || _0x150847["gSpKG"]);
  }
  const _0x1574d5 = _0x1a6147["url"];
  let _0x486b4c = _0x1a6147["type"];
  if (!_0x486b4c || _0x150847["NNdka"](_0x486b4c, _0x150847["sIxVV"])) {
    if (_0x1574d5["includes"](_0x150847["IrWmm"])) _0x486b4c = "m3u8";
    else {
      if (_0x1574d5["includes"](_0x150847["HNPRe"])) _0x486b4c = "flv";
      else {
        if (_0x1574d5["includes"](_0x150847["rELHw"])) _0x486b4c = "mp4";
      }
    }
  }
  return { url: _0x1574d5, type: _0x486b4c };
}
function showPreRoll() {
  const _0x42dee9 = _0x2b2717,
    _0x3b1fc2 = {
      rljvA: "_blank",
      QbWRp: "flv",
      gpiFb: "art_skip_outro",
      SyIEm: function (_0x2b3136, _0x2e2ace) {
        return _0x2b3136 + _0x2e2ace;
      },
      DwlkO: function (_0x22aca5, _0x1448f2, _0x554fce) {
        return _0x22aca5(_0x1448f2, _0x554fce);
      },
      OUOdu: ".art-contextmenu-item",
      bIlpg: ".art-contextmenu-version",
      WFCSg: function (_0x44a686, _0x4e34a1) {
        return _0x44a686 === _0x4e34a1;
      },
      opIAG: "BAzgE",
      GXlsc: function (_0x5465db) {
        return _0x5465db();
      },
      nCQUY: function (_0x2aeecd, _0x3b5597) {
        return _0x2aeecd === _0x3b5597;
      },
      ZHnwM: function (_0x4aae98, _0xfc7f40) {
        return _0x4aae98(_0xfc7f40);
      },
      CEKZT: function (_0x4d09e7) {
        return _0x4d09e7();
      },
      BuHJP: function (_0x4e97d9, _0x2fb709) {
        return _0x4e97d9(_0x2fb709);
      },
      QCVrW: function (_0x51d297, _0xb49e87, _0x4b7828) {
        return _0x51d297(_0xb49e87, _0x4b7828);
      },
      pQcAS: function (_0x463f1c) {
        return _0x463f1c();
      },
      KVoAt: function (_0x1c5aec) {
        return _0x1c5aec();
      },
      hYaeU: "ad-pre",
      GgOGi: "ad-pre-timer",
      Oglgx: "flex",
      tvQMQ: "video",
      mYDWe: "hLVwZ",
      gZMgM: "zzNbc",
    };
  return new Promise((_0x3594e7) => {
    const _0x55a031 = _0x42dee9,
      _0x3cace1 = {
        UMfCt: _0x3b1fc2["QbWRp"],
        CoVxZ: _0x3b1fc2["gpiFb"],
        CMnNZ: function (_0x54f969, _0x837f3) {
          return _0x3b1fc2["SyIEm"](_0x54f969, _0x837f3);
        },
        HJqbp: function (_0x4a4dac, _0x4926b1, _0x58a1b4) {
          return _0x3b1fc2["DwlkO"](_0x4a4dac, _0x4926b1, _0x58a1b4);
        },
        NdXVz: "跳过片尾",
        qarkF: "none",
        RMbDO: _0x3b1fc2["OUOdu"],
        lyhGw: _0x3b1fc2["bIlpg"],
        ceapk: function (_0x394c53, _0xd9df2a) {
          return _0x3b1fc2["WFCSg"](_0x394c53, _0xd9df2a);
        },
        pXCIV: "AnGti",
        YJBtr: _0x3b1fc2["opIAG"],
        YDuDF: function (_0x5ce094) {
          return _0x3b1fc2["GXlsc"](_0x5ce094);
        },
        Dpcju: function (_0x1497f7) {
          return _0x1497f7();
        },
        apxlg: "loading",
        fDjuw: function (_0x538615, _0x466165) {
          const _0x57f1dd = _0x55a031;
          return _0x3b1fc2["nCQUY"](_0x538615, _0x466165);
        },
        CrXYG: function (_0x32c849) {
          const _0x3f078f = _0x55a031;
          return _0x3b1fc2["GXlsc"](_0x32c849);
        },
        jJkgU: function (_0x421c65, _0x1bb660) {
          return _0x421c65 === _0x1bb660;
        },
        yXfex: function (_0x3cb5dd, _0x512009) {
          const _0xde9db8 = _0x55a031;
          return _0x3b1fc2["ZHnwM"](_0x3cb5dd, _0x512009);
        },
        PGiTX: function (_0x1512ad) {
          return _0x3b1fc2["CEKZT"](_0x1512ad);
        },
        npCZx: "JJPZu",
        CcDUX: "XdLWX",
        Xiluv: function (_0x54dbfb, _0x32115f) {
          const _0x5d19b6 = _0x55a031;
          return _0x3b1fc2["BuHJP"](_0x54dbfb, _0x32115f);
        },
        lJNFw: function (_0x37681c, _0xa25aa7, _0x14ab40) {
          return _0x3b1fc2["QCVrW"](_0x37681c, _0xa25aa7, _0x14ab40);
        },
        dBBFb: function (_0xa01434) {
          const _0x352bf4 = _0x55a031;
          return _0x3b1fc2["pQcAS"](_0xa01434);
        },
        eaObd: "加载中...",
        oepox: function (_0x7315d9) {
          const _0x1079db = _0x55a031;
          return _0x3b1fc2["KVoAt"](_0x7315d9);
        },
      },
      _0x3af9e0 = playerConfig["ads"]["pre_roll"],
      _0x386cf0 = document["getElementById"](_0x3b1fc2["hYaeU"]),
      _0x445a0a = document["getElementById"]("ad-pre-container"),
      _0x3d6208 = document["getElementById"](_0x3b1fc2["GgOGi"]);
    _0x386cf0["style"]["display"] = _0x3b1fc2["Oglgx"];
    let _0x4ac30a = "";
    if (_0x3b1fc2["nCQUY"](_0x3af9e0["type"], _0x3b1fc2["tvQMQ"])) {
      if (_0x3b1fc2["WFCSg"](_0x3b1fc2["mYDWe"], _0x3b1fc2["mYDWe"]))
        _0x4ac30a =
          '<video src="' +
          _0x3af9e0["content"] +
          "\x22\x20autoplay\x20muted\x20style=\x22max-width:100%;\x20max-height:100%\x22></video>";
      else {
        const _0x58b4fc = _0x355154["createPlayer"]({ type: _0x3cace1["UMfCt"], url: _0xbd09bb });
        (_0x58b4fc["attachMediaElement"](_0x5925df), _0x58b4fc["load"]());
      }
    } else {
      if ("zzNbc" === _0x3b1fc2["gZMgM"])
        _0x4ac30a = "<img\x20src=\x22" + _0x3af9e0["content"] + '" style="max-width:100%; max-height:100%">';
      else {
        ((_0x4909b2["skipOutro"] = _0x3f4b72), _0x4492ec["setItem"](_0x3cace1["CoVxZ"], _0xe8d18d));
        const _0x4ace08 = _0x2fe61a ? _0x3cace1["CMnNZ"](_0xbaf185, "秒") : "关闭";
        (_0x3cace1["HJqbp"](_0x57b67b, _0x3cace1["NdXVz"], _0x4ace08),
          (_0xabc52["notice"]["show"] = "已设置跳过片尾 " + _0x598afb + "\x20秒"));
      }
    }
    ((_0x445a0a["innerHTML"] = _0x4ac30a),
      (_0x445a0a["onclick"] = () => {
        const _0x4865d9 = _0x55a031;
        if (_0x3af9e0["link"]) window["open"](_0x3af9e0["link"], _0x3b1fc2["rljvA"]);
      }));
    let _0x21d7d9 = null;
    const _0x3d3b82 = () => {
      const _0x5905cb = _0x55a031,
        _0x1f18e1 = { WiauD: _0x3cace1["qarkF"], tFNiX: _0x3cace1["RMbDO"], bZYlA: _0x3cace1["lyhGw"] };
      if (!_0x21d7d9) {
        if (_0x3cace1["ceapk"](_0x3cace1["pXCIV"], _0x3cace1["YJBtr"])) {
          const _0x472812 = { AjyoU: 'a[href*="artplayer"]', lpEKV: _0x1f18e1["WiauD"] };
          _0x2a0d3d["querySelectorAll"](_0x1f18e1["tFNiX"])["forEach"]((_0x3f6431) => {
            const _0x15c090 = _0x5905cb;
            (_0x3f6431["textContent"]["trim"]()["includes"]("ArtPlayer") ||
              _0x3f6431["querySelector"](_0x472812["AjyoU"])) &&
              (_0x3f6431["style"]["display"] = _0x472812["lpEKV"]);
          });
          const _0x5ec48b = _0x464b83["querySelector"](_0x1f18e1["bZYlA"]);
          if (_0x5ec48b) _0x5ec48b["style"]["display"] = "none";
        } else _0x21d7d9 = _0x3cace1["YDuDF"](resolveVideo)["catch"]((_0x3d0711) => ({ error: _0x3d0711["message"] }));
      }
      return _0x21d7d9;
    };
    let _0x4990e7 = _0x3af9e0["duration"];
    _0x3d6208["innerText"] = _0x4990e7 + "秒后跳过";
    const _0x3e06ca = setInterval(async () => {
      const _0xf3e14f = _0x55a031,
        _0x421bda = {
          GmNWC: function (_0x240167) {
            const _0x42f7b8 = _0x12d4;
            return _0x3cace1["Dpcju"](_0x240167);
          },
          dzvQs: "loading-box",
          GjoJE: _0x3cace1["qarkF"],
          AWDFJ: _0x3cace1["apxlg"],
        };
      _0x4990e7--;
      _0x3cace1["fDjuw"](_0x4990e7, 0x1) && _0x3cace1["CrXYG"](_0x3d3b82);
      if (_0x4990e7 <= 0x0) {
        if (_0x3cace1["jJkgU"]("Zfwca", "pdgZG")) _0x421bda["GmNWC"](_0x5389de);
        else {
          (_0x3cace1["yXfex"](clearInterval, _0x3e06ca), (_0x3d6208["innerText"] = "加载中..."));
          const _0x597a8e = await _0x3cace1["PGiTX"](_0x3d3b82);
          ((_0x386cf0["style"]["display"] = _0x3cace1["qarkF"]), (_0x386cf0["innerHTML"] = ""));
          if (_0x597a8e["error"]) {
            if (_0x3cace1["ceapk"](_0x3cace1["npCZx"], _0x3cace1["CcDUX"])) {
              const _0x247797 = _0x114962["getElementById"](_0x421bda["dzvQs"]);
              if (_0x247797) _0x247797["style"]["display"] = _0x421bda["GjoJE"];
              _0x164e6b["body"]["classList"]["remove"](_0x421bda["AWDFJ"]);
            } else _0x3cace1["Xiluv"](showError, _0x597a8e["error"]);
          } else _0x3cace1["lJNFw"](initPlayer, _0x597a8e["url"], _0x597a8e["type"]);
          _0x3cace1["dBBFb"](_0x3594e7);
        }
      } else _0x3d6208["innerText"] = _0x4990e7 + "秒后跳过";
    }, 0x3e8);
    _0x3d6208["onclick"] = async () => {
      const _0x42064b = _0x55a031;
      (_0x3cace1["Xiluv"](clearInterval, _0x3e06ca), (_0x3d6208["innerText"] = _0x3cace1["eaObd"]));
      const _0x468db0 = await _0x3d3b82();
      _0x386cf0["style"]["display"] = _0x3cace1["qarkF"];
      if (_0x468db0["error"]) showError(_0x468db0["error"]);
      else _0x3cace1["HJqbp"](initPlayer, _0x468db0["url"], _0x468db0["type"]);
      _0x3cace1["oepox"](_0x3594e7);
    };
  });
}
function _0x1a56() {
  const _0x3330df = (function () {
    return [
      _0xodD,
      "nKTWjwsUjEfiqhafnmDig.gcWHobmrFQ.Fv7KTqP==",
      "n3tdLCkLaqVcRa",
      "ymoormomzelcNdJdSSk+i8khW6VdJXXoha",
      "cSkgC8oUDG",
      "WOpdU8kCWOFcRq",
      "WONdTCkQ",
      "WRjnWOqpavpcS8kHW6q6vazqWQ1vESkQFwxcIqf4WQW",
      "mruAb8ozha4",
      "eSo6W5jBBa",
      "kgzZWRTV",
      "WPVdNmkSt3W",
      "W6JcHuT3WPu",
      "vSorW60zaq",
      "cYhcIgPp",
      "pSkAymoPv8kRcCoZz8oXwW",
      "tCkuWO/dRgS",
      "WPZcMbxdImkC",
      "W5WBWOdcOam",
      "WQiGW6Djiq",
      "tmk8sMO",
      "FGieWO5jWRpcJtC8",
      "WQCLcfGb",
      "omkhW4mVbq",
      "xWn1umkc",
      "qCoXdSk1pmoLyq",
      "gCk3umoDCa",
      "5B+L5BUF5O+55lQi5yUU6l2S5yw56zsyqG",
      "WOBcHKFcI00",
      "wc58cSk6WPpcGCkiWPxdV8kcW4CPaq",
      "mCoSaSkcWQRcU8ovzhO3W7W",
      "W5jZW6uj",
      "WQ/dVLiskW",
      "CrjKeMLHW5vjgNbxxW",
      "WR/dM0TQWPK",
      "k27dH8kP",
      "l2tdHCkjwmoPWO/dNSkREJC",
      "W7CVjrNdTbjltW",
      "W4ZcTmoZWOe8psC",
      "W4H0W64c",
      "WQ/dK1rlWO4",
      "qmkOWQ7dNKrqAq8",
      "WRlcKmkVEZ0",
      "WPnCWO4xcW",
      "WRldPv8xlxq",
      "xcDPpmkLWRRcHCkEWO8",
      "WROBg2Gu",
      "WPRdImkADMG",
      "dCkzFJS",
      "WRtcT1pcHxS",
      "WQNdUKmFbW",
      "W6GOiHddRInCua",
      "m8o+iSk6W5a",
      "vSkIWRFdMKDC",
      "m8oPcmkCWQG",
      "WOKulNys",
      "WOZdNMviWRpcR8opW51DE3FcNSkz",
      "dmk0vIa7",
      "e8kYAcGq",
      "5OkG5AAh6BQ96k6R",
      "ph7dGmkihadcPG",
      "WR/cPCkfWPi",
      "amk2W5eSjG",
      "WOb1W6ylWQdcJfGcWPK2",
      "W4/dKwJdVmkD",
      "W6yZWOa",
      "WRyDW5bTjG",
      "iemsDxG",
      "WQBcSv7cTM3dRSoUWR/dGCkZW6qGWQ7dNW",
      "rmkPWQtdTg8",
      "AqfLyCkozSks",
      "mv8MrW",
      "W60TWRhcLsW",
      "W6ddVeiAk37cO3ikoCoGW6a",
      "p0noWR9N",
      "ph7dGmkebadcPSorWRqqqCo3WRVdOa",
      "C8kCuKTw",
      "jCoIW5fF",
      "nbnbW53cKG",
      "WOSLd2yAWRG",
      "pMNdHSkUgG",
      "WPPk56sN",
      "g8oda8kcWRy",
      "WPVdVmkXC3lcO3lcIa",
      "W53cGe1VWPKbpSkfbceqdmk0",
      "WP42W6rOaColj8kgemoeW6Xsvwu",
      "AGf5zCkc",
      "W6H3cSkmdGW",
      "rSo5dSkX",
      "gMZdKSkyDa",
      "cmk8W7pcSX4",
      "WOtcOg7cVey",
      "WRxdKvrBWRm",
      "WQtdJSkuWP/cLa",
      "cKS4teK",
      "WRNdNSkvA28",
      "k2tdN8k8Aa",
      "DCoPW6W4nq",
      "pSo2eCkuWPZcUSouqNa/",
      "WQm+W5pcTSo1",
      "WQ7dPqzK",
      "WQH5dmkrqaRdVCoMi8o+W4tcJqvPW53dL2BcOCogWOtdMG",
      "nvfBWOjt",
      "WOWRW6vN",
      "WO7dGgLkWOxcICoEW4nx",
      "uHlcO8kT",
      "5BAP6lsH6l2154Qv5Bg4jG",
      "vqBcOSk4i37cGSkX",
      "W5tdG3/dNmkY",
      "W4VdGCkPWRxcP3m",
      "hX7dO8kSBW",
      "k3FdLCk4cGtcQmoFWOGfD8oR",
      "WO03gea+",
      "oh5RWQr5aGPUeW",
      "mCo9m8ksW58",
      "W5f5W68fW6e",
      "dSkdW7qimmoakSo/WOS",
      "WQ9Ml8oTW7KnW4lcVmkAzMO6W5e+",
      "W50pWPdcOr9ECCoiW4Kon8oXaG",
      "5Bw85OIN5Bkf5yUK6k2P5Asr",
      "W6mUWOldGCockKLEpCk7WPnYs8kIWQldP8klWR4",
      "pmkiW7/cTqS",
      "W4BdT03dRmkOW5pcQsZcVKRcP8kfFWq",
      "WQFcO8oLWQ7dHG",
      "WR9SoSoH",
      "5PQc56sM5y6X5z6Z",
      "ggddJSkjwmoPWO/dNSkRBdC",
      "tcbHp8kzWOpcMmkFWPq",
      "W7DTg8kxfdRdT8oKmSo4W4JcLHO",
      "WOxcRJxdRCk/WPtdICka",
      "z8k4W7LBC8oyW4q/",
      "W4T7W7WEW4W",
      "WR7dNmosjCkJW5yY",
      "Bw/cLSkPDmk8F3y",
      "WOFcHCouWRxdNCkRrSkmWR7dM8kl",
      "wmo2CSoNzG",
      "WRrTpCo0W6KAW5pcNa",
      "WQ3dNCkJWOpcSW",
      "5yUL6l2B5lM7dhD2",
      "aYjLkmo2WOxcNSkoW4BcQCkPW5mhsSoYWPldOLddP8oqW4TCzr/dSG",
      "W5RcR115WO0",
      "W7vZdmkKlG",
      "WRZdNCkWWOlcSJhcG2hcRCoNeSo/WQqRjG",
      "sCoHfCkcjW",
      "WOFcLmkuFtez",
      "jej7uJGTW61h",
      "oJVcQmkasa",
      "W7tcKwrkWRG",
      "AGz5DSkUzSkvvIK",
      "WONdSK1zWPa",
      "W6JdNCk4WPhcTNxcVG",
      "yIe5n8o6ndZdGCoyW4NcKX7cJ04",
      "WRtcQ0xcNG",
      "WQuJW6dcSCom",
      "6lAV6l6q54Qv5BoU",
      "W6DOdSkaaW3dKCoGpSo3W5G",
      "dH3cQmkCBW",
      "WQ5MkSorW6GBW5S",
      "WRKSW6BcU8oA",
      "h8kbD8o0xW",
      "W455W6ydW7BcMG",
      "b8k5W6CVnq",
      "n3TKWRW",
      "oIlcVSk8F8kSswPlBW",
      "W7e/WPpdIW",
      "W4eCWOpdJ8oc",
      "W4PWd2ymWRNdGmoPxsTsWQZdPYW5WRmJjX9bWRjsWP0sqdhcT8oOcmkBW5/dQhVcTIJcPc1ym8kLC8kM",
      "W69Pc8kPdG",
      "orRcP8k4tG",
      "WQtcL8okWRxdQG",
      "CGagWPftWPZcJW",
      "WOBdT8kSDMO",
      "l2NdLCkVgWpcPmogWRC",
      "WRVdR187iNtdRMqwlSkFWRVdUKi",
      "A8oRg8kqkq",
      "W63dTSkOWQBcUW",
      "jLqZqY09W5Tomw9zwsm",
      "WQumW5dcPCoR",
      "EInRaSkv",
      "Ft0/lCo2osm",
      "earOW6JcUa",
      "zmolDCoKra",
      "dK7dOCkzhG",
      "WQJdO18skW",
      "W7ODWO/dQSor",
      "FCowW6C/ga",
      "WQVcICoaWRtdQa",
      "DxldL8kUbKJcP8oBWRKp",
      "WOevm1CS",
      "m8kaFmo+",
      "r0G1sG",
      "WQZdJ8ocl8k9",
      "aCo3mCkrWPC",
      "W49OW6qCW5dcJuurW4vZi8oOWQHxrG",
      "W7zQg8ktcaFdPSommSo9W53cJar4",
      "WQtdGmk2",
      "vHqBbCoi",
      "WOtdJhr9WQW",
      "jeO1vsK",
      "dCkAEdWhwmoosSkB",
      "oCo/W4HkACkfWRPOBCoBWPu1mwXSWQZcK0pdVSkEuSoRjrPPW6pcOwNdSSoUhSk/jmkW",
      "W6RdK8kKWRNcTN3cO13dJwpdRq",
      "W4ivWPVcTG",
      "eSoTeSkCW4e",
      "z8otu8oMzW",
      "lLqbrfO",
      "sCo3hSkU",
      "cuuSBsS",
      "WRhdOrDoWRS",
      "hCkqzs8G",
      "W4vSWQZdR8kkWRG0W7CWWPhcGW",
      "WPq5W7tcPmomWReEW7ax",
      "jComxmoYBuVcJW",
      "WRpcOCkqWPC",
      "nK45vq",
      "oHtcHMfs",
      "WRNcR8kqWP8/xq",
      "W7GUndddObvg",
      "hXfRW7BcUG",
      "WQpdUbf/WPrewCoAWQ0zEMOvaSksWPlcQmoMxdDyuG",
      "iCoNW51dEmoEW7ySsmonWPz+",
      "c0eRweCKW5noW4hcOMS",
      "W4dcMKL5WRm9lSkBaIC",
      "WQLMjSoS",
      "W4/cMKzPWOuQl8kebcWr",
      "ymomqmo2EKRcVINdUCkZja",
      "kmk6W53cPq",
      "WOe8W7hcSSoqW4ulW7qFWPZcK8o+WQmlWPZcOa",
      "WRVdM8k+WPZcKs/cJwxcQCoyw8k+WR08yq",
      "WPZcRcpdPSkJWP7dNW",
      "Cf0qW4u",
      "WOrbWOqlaKdcRW",
      "WOy/eNC",
      "kmk5W5VcOG9Oeb8C",
      "W7jEmmkmnq",
      "f8kRWQxcMHWfkq",
      "W7CVkbddSYjlreK",
      "EYOHWQvk",
      "smkPw3zXW4DgbxVdL8kDpG",
      "W4/cUSoKWQqq",
      "j8oTmSknW5RcJLNcQdtcUSk7nCkCtxJdOCoCoGKmW7if",
      "cJdcNgLCW6u",
      "6lAO6l+v54Mn5BoP",
      "Aq8xWPPFWOS",
      "W6rKW5m4W5i",
      "WQfIWRKxaW",
      "ew/dKCkteq",
      "k8k+W5pcQYrNbWyHWRLoaG",
      "W6edWP3cHGa",
      "muCKrtWS",
      "WQlcImojWPldTG",
      "l8kRW4lcTW",
      "W6pdHeZdMSkt",
      "WPJdK8ohg8kH",
      "umkyWRldIMm",
      "W5RcT8o0WQm0mdW",
      "ge8Rv2q",
      "kCoPcCkiW6e",
      "FmovW6yOfHXz",
      "FmkIB2v3",
      "WOqmW7JcNCok",
      "WPlcKSofWQdcS8kOsCkAWR7dMq",
      "wCo+WRBcLG",
      "s8oJW7O6aq",
      "nunCWRPg",
      "WP0WW7HYaq",
      "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",
      "eb7cLxrE",
      "W6OUnG",
      "mCo2hSktWQ7cOq",
      "WQNdMSkLWOm",
      "nxtdMSkK",
      "ktNcHfrg",
      "g8kgW7eEla",
      "W4H8jSkZfW",
      "WPVdSmkXzG",
      "BGSrWRXoWOVcLI0QWOZcQSoW",
      "WPPKWQ8inW",
      "WO/cR8kNWOyZ",
      "cCoWdZyNWPCtov7dNmkqgCkn",
      "W43cUCo0WO0t",
      "amkAW6eEjW",
      "lZlcPSkzEmkQvG",
      "WQ3dV04mn0ldPM0DoCkPWQ3dGq",
      "gGzzW6xcNcFcO8oBWRKh",
      "mW8xWOKxWOZcGta8WPdcSmoYW77cKmkBy0bzW4ddHG",
      "wmovW7eshG",
      "WRVdQCkLwvC",
      "5PsI5RgF6kAg5P6F6ks+6Ak044cI",
      "rSkOWQ7dGv5u",
      "5BAP6l+f5OYr5OMu5BcN6k+B5AEm",
      "vSkQtMzWW4m",
      "dubKWQje",
      "WO/cS25BWQyuhq",
      "WOnhWPKDb0y",
      "bCovg8kGWR8",
      "WOFcImoKWRpdRG",
      "bSoyW6HzyG",
      "W5CJFSk4WRXEWPBdJ8oFkx06W4HWi8kGW4Wrfmo0WPO4zCo+ySkypSk8oCo8W7BdGaXSb2DpimkXW7JcItalW4RdTmkpWOldJhzdrv0pEtzXxSouW6FdJ0uFWR9lzSkQAmoGWRddJfr8qb8LysrwWQFdHSkKntrsWOFdHMOaqc4FyNLQAComW7btdmklWQFdTCk9lJpdOCo+WQnMxqWto8k5WORdTLRcLHRdGmkweSo+WPiMWPVdR07cPSk/vGOnyIJcJsRcKKjnWQa",
      "DaagWPfpWPVcGtC",
      "5BAF6k2r57+76lAi6l6e54Ul5Bg9WQW",
      "dmkuEYKRwq",
      "ESkeqgHw",
      "d3NdPmkTda",
      "hSkkW6eYn8oPlG",
      "sY0dWQrW",
      "oIxcS8k9ACk4vh1f",
      "WRZdUSkQwKO",
      "WP7cJ8ozWRldU8kGr8kpWRu",
      "hwT7o8kVWPRcICoqW5NdPSkHW4zneSoOWOldT0ZcUmopWOGAjWBdRmkea8kxWO/dJmkaWRWzfM4ejSkYWQFdTctdVG",
      "W6NcQKNcHNdcQmoYWQhdSSkZW7i/",
      "WOTodmoCW5y",
      "kSoWj8kzW5/cGuC",
      "WQ/dQvKxpMu",
      "dmklW6y",
      "nuO3wZS5W71jbMniuG",
      "W5JcUCoOWOS0oceaF8k4WPK",
      "nSoUW4H5B8onW6CIDmoyWRf+l35MWQdcKa",
      "b8oGi8kiWOK",
      "WQ12lCoW",
      "56sv5zon6lEz6lYU",
      "WOe0W4HFiW",
      "tZ57jW",
      "W7xdUx/dImko",
      "ednFW47cMq",
      "p8kjEaqU",
      "WO3dQcbNWQ4",
      "WRPqWRSHjq",
      "qCk/WQ8",
      "5OUR5Bk+5yIm5AAh5y2E5AsC6lAF",
      "nmo6k8ksW4dcIG",
      "W4JcNfTTWOWZiG",
      "WQRdT8k2C1S",
      "W4eXWQddRmoa",
      "xmkbWPxdMxi",
      "WRnSkSoXW78B",
      "WOVcISkGvaO",
      "ySoSi8kjW4lcHK7cQG",
      "nt3cPCkAFq",
      "WOJdMwW",
      "W4/cLfX+WOG",
      "WOhdOtndWPK",
      "nSombCkfWQm",
      "Dmooxa",
      "qmoWD8oruW",
      "dXBcG0nE",
      "oSkIW4lcTYHIjWuAWRrE",
      "5BER6k+t572+6lE16lYG54Mp5BoFba",
      "W6LQf8kaaX3dS8o8pSo0W5i",
      "m8oRbmkVWQlcOmovvxC",
      "peGqCvu",
      "ggZdGSkrFG",
      "W7xdSgNdHCkG",
      "W4JdVfFdJmk2W77cKatcNa",
      "gKSTDvyZW70",
      "tc58bSkIWPpcGq",
      "lYpcQ8k8Aq",
      "mwJdM8kV",
      "vd7cPCkXfq",
      "F8kbFxzA",
      "v8oWW6qmpa",
      "W40rWPRdTSon",
      "5OU85BgH5AwO6lsz77YU6k6H5Qgq5P+e6kYt5AEk",
      "i8kwW5JcQb8",
      "W6hdGmkJWRhcUwlcT3BdHxZdQG",
      "x8ozWQbiD8o+emofWP4yWPG",
      "WP47W7BcU8okWPSAW64",
      "nK0/uHa2W6PqoW",
      "xColpmkWbq",
      "amoxj8ksW54",
      "Dr4BlCoW",
      "5P+g6yoj5OQ/6kY/5AEn5OUM5OI55Bk85lQF5yYP55Al",
      "ngrfWQjD",
      "oMVdHmkKbGhcImoCWRmizW",
      "56s95zkx6lsV6l+e",
    ].concat(
      (function () {
        return [
          "hqzmW5FcJZ/cOmoCWR8",
          "AHL/DSk3ESkovcFcRmkLB8k3f8kw",
          "W4ekW4e",
          "WQxcIrddHCk5",
          "W68Gnb7dHW",
          "xrZcTW",
          "aWD+W4dcQa",
          "WPXXo8o5",
          "WRhdOqX/WRDqvmonWRa",
          "v8kHWQRdJum",
          "WPWRW7v/emoa",
          "W7NdGmkmW6hcVSoKcmoyW7VcICoEftOa5BYT6zs25zMp5QcFWPDoWPNdPKtcNmogACoXxbpcHmkYwCkjmLJdP25uA8k3iSogWRpcLbnhpSksW6fmic1Bq8otWOGUWPpcUdO3ACktW7FdHSoaEGCJW6y/CsNdT8kpWPNcRmk/sSo5FxrjkCo8WPFdVW8/WQJdKSoBuIyEWPdcGIyKWOvYWPpdTCkdWO7dHIqihMO/oSkhosNcIrRcG8oTWRGMrf0ImCkqW57cQIpdR8oil8kdmG0MbCk7W4jmWQldONK9FbZcMGbYWQyShCocs8kWW53cTZfzWPboWPZdKmo7Dmo4WP7cTSkxeSkxWPpcICk3qmkHjmkbWRhcQYWMWQ1eW77cPmkECmknWPBdRbqWtCo1BgpcNSocqCk5WQzHqfRdOCopWO9NW44uWOKUf8oZWPNdMCokWPpdVSktumkpiSknlmoaj2HrW74Cy8odW5WhW413uSoUW7ddMrtdP8o1CaRcRCo9WPRdTmobmq7cKXX7rHeFsCkvWQHMWQddNmkrrSk/WQz0iSorhWtcOrilWRlcIWVdIZFcHG1gWPRcL8ofo17dIfW5eCo9g2VdTaZcQmotWQ/dRmofASk0WPtdJmosWRrDemogW7hcLYhdL8kiomkyW5ylvbxdHSkBkCkiW7S/kSkODH0hm8k0WRTvgEMwG+MuKowzMUAIJsJcHWldVmogW5hcH8ohWQxdNhbJWRtcHCkoW4pcKtBcR8kbW6jnd8o9W7/dGmo9wCozhZpdRNldLmk2WQ/dOGdcLGNdUSkLtSo6h8kGgXDMCCk7W7xdHCkkq8kqWOLSfmkEn8ooWQ0PgCoRWOCFW6O5BWbkaSkTzXBdKCkQW5ldKqhcHSoYaMxdQdaEW4VcHmkfDZ1/e8o+WPXZaW0lW4NcL8k4WPpdSmoMma5vuH/dLdxcM8kTuZFcHSkskey0WRaFrWKvW44/W6VcLSolbcZcRCkxW5etn8oKtSo4WO3cGW3cOmoNevfhW6bHW47cMYv9WOuIodDgWRNdG2tcS8k+WPJcR8k0WOdcJxqbt1jhlaj8WPddNGjPn3JcMg5hjWNdHI4OhJbsmCk/DstdLwpcJefAstKmW7icW7xdVvxdSmk8DY7dLSkdWPaYW5/cRdC4WP0admo6t8oGW5hdICoBDCkEWOpcUxGZW4STWPnTuwhcUSkGWPtdGs5EnqVdLHVcMJpdKxJdRSoEdw9hWQnGx8oucs7cHSkXzSkkWOu6qmolqmoQW7DhErxcJrldKCkgW5pdJwxdLZfTWOHkW4xcRqtcMI4EW4RdUHpcR0ZcT8oRW4yDWOddMHhcImoyW63cHmkoW7yFWPddUCo0eu7dI2HUW6NcJarGbCksW5qKEmolbCorfJpcGCoPl8oAW7nbEdC2WQlcHZy1WPFdGSkWAmouW7X2WPpdSmoWWQZdJmodWOVdO8oJWOutpCotWQuAuveMWQ/cRSkGWPBcP3fw",
          "WRJdNmkfvK4",
          "hCkdW7qciCoTimoNWQ0PWQeA",
          "hgiFwHa",
          "W4qvWPVcVbq",
          "WQlcMtRdGmkR",
          "WO4afx07",
          "WQ7cRutcJgZdKCoIWRFdQG",
          "vmo+zSogvG",
          "WRxcHb/dUCkd",
          "W5jZW78fW6pcMG",
          "cmkDW6Cumq",
          "DtyOcmoRpYu",
          "nWbGmG",
          "WOq/hxyCWRVdGSo5hsLl",
          "t8o1l8kKba",
          "W59WW6OFW7pcSuSmW4e",
          "W4SnWQZcLYi",
          "WOxcRJJdPmk4WQtdICklW6y",
          "emoXbCkpW5m",
          "WRpdVWb9WOf2rCotWROQyNaa",
          "oCk+W53cSs0",
          "omoLW59wB8oBW7a0",
          "habLW43cOq",
          "lJlcV8k/ESkQ",
          "WP0VW6HUk8oqj8kWgG",
          "vmkGvgHNW44",
          "WP/cHCocWQBdQSkS",
          "f3H/WRz9",
          "WO8GW6vBeSoapCk2oColW75txh/dHSoi",
          "W6yfla/dMa",
          "kMC/ANy",
          "Btvcr8k2",
          "oMNdGmkEdatcPCozWRSpDSorWPpdTSk6hW",
          "nmk3W4lcVt4",
          "WOZdRmknDfy",
          "cGfiW4JcKXVcQSocWRebW4qBuCoaW6RdSG",
          "h3nKWRPRjX4JpSknhce",
          "WPZcUmkmAau",
          "WPNdPf8Bpa",
          "WQpcPCkCWOjZuSkMsmo5v8kXqmoTWRe9",
          "cSkdW7JcKqa",
          "kmoTh8krW5G",
          "d1pdG8kVja",
          "W6ldNCkRWRdcMNpcSMVdJq",
          "dxFdGSoqD8oPWOldGCkRzM5IaWtdHW",
          "jfiIqZOWW5nhmgTDCJSSW6ddKfnH",
          "W4ZcSSoQWO0V",
          "rrxcQCk4oW",
          "o1pdSmo5DZFdJCo/rZ9iEIrYW5bnW7lcRmofvmohW57cVCoEdqZcHSkXxx7cUv7cJSkXW64qD3pdVxytW7PsfmkOoCoFFNpdQSkshSoEoSovWRSWWOODWRLJWPddHCk1W7GTW77dIJTxrI9XW4xcOmoTWR0UvmowW5NcMmoMW5SxW5uaW4uikarXlCkbWQqfW6pcHGhdPSoWzCkqWOzPF8o/WOCRfmkEpgtcMCo0W5G3W4BcMXq2y8obkmoGe8oKi3f9W7pdSf3dSf8zxSo8fe7cRq",
          "WOVcJSkpDZiiWPJcLaaAW6K",
          "dCkAEdWbq8oosSkB",
          "WRBcRSkOFry",
          "WPRcJSopWQ3dQ8kGtCkl",
          "sYjLkG",
          "WOldOCkDWORcJW",
          "WQtcOKtcUxldPmo+WPVdP8kSW7q",
          "u8o5eCkWnq",
          "W4KmWPNdOCov",
          "kCkhD8o1",
          "n8oIW5boF8on",
          "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",
          "WPRcK8o/WRtdRSk0r8kkWQ/dKmkB",
          "EcfNbCkt",
          "WPWLW695aq",
          "5PY877+N5y6n5Awq",
          "bKqEvXm",
          "fr3cHwjy",
          "rHGwmSoP",
          "WP0HW6r1",
          "W4xcM0z4WPigpSkrfq",
          "nSoTkSk2W6i",
          "lMbM",
          "WQNdJmoudCkJW5OWAG",
          "W7NcRCoxWOnK",
          "WRBdVxnpWOy",
          "dHPbW5xcIsm",
          "DSouW6y5atP5WQa/",
          "WRBdUbbQ",
          "WRNdVmknD08",
          "k0KIsZO9",
          "FIKbWRv/",
          "WOZdUmkVDW",
          "WRBcK8opWQddRSkH",
          "qbrOqmkR",
          "sbdcKCkviW",
          "WQ9ggCo0W68",
          "WQBdLqG9W4bYE8ojqx4xfCkHW6qQW5NdKmoKj8kAWPDfsHzLW5biW6RcHvBcUhldMuD5CmkKvmkYW6z2W4JdQs7dVCoXy34RWP7cJNCqAdFcKHSfkSknWRHGWO5EW5uQW7bTWQlcVeZdP05ieSoTw8k0WPCFWQJdU2z6nrjGW5rpBmkVxN/dGtiHW6lcHZ/cHCkdWPFcKtPbWPxcGXpdOI1dm8kgW4ukr8kfw8kNW5NdNSoGWPldJCkgotWIkGldLxpdRwtdQIe+oYVdHCoUfCkDArCdF8ong2q6i8o6WQ5zW4qocmoFjqhcG01FWRNdK8kIgXBcINFcOLDRob5klXz3WRVdTtmYW7tcV8kCacNcJKRcRH0pgcldHfZcICoTEhHaymklWOJcOCkkW7BdLSokr8oEWQpdJ8orCdu4W4O3WRlcQCkFWPK7B8ojWO9RWOJcOmosWOhcVuVdGJddRCk7wSkhu3WdaSkhsWf5vCkOd8knWQ7dPexcTwRcQfuFW6ZdKu/cGmoOW6ldTd7dICo6bqxdJmoOySkvW7K9x8kJW6SPW7eqj8kRnmo4r2jAWR0ZWRG4kCkkamodo23dJ8oTWP1qWPr+W5NcQSk8WQCQWOzaoYHBW70fW5rGW5irefPLtSofW4JcM8o3WPK8W7vDW6hcTWOiimkPW7aiAuKvxX/cNhNcNhqV",
          "m8oKW5Hd",
          "WRjZo8o2",
          "n8k3W5ZcTtjU",
          "gbTjW58",
          "ASkiweTC",
          "oSkGW4BcJtvTdr0SWRDpe8kIW7i",
          "uaxcTmkApq",
          "xbytimoT",
          "WOpcPCk3WQW+",
          "jmo5fmkNW4i",
          "WPZdJY1kWQVcICozW5q",
          "W6u/WOldPConj2LEn8kMWRboBSkJ",
          "WOFdU8kRWO/cIa",
          "WPZcLSoQWOFdIa",
          "gCo6nCkyWQ0",
          "kCk3W5/cVtbJ",
          "W4lcR0T/WOu",
          "dCoDkSkxW7W",
          "WO3dOhWojq",
          "WRhdVHXJWP0",
          "FbWrW5bzWORcLZaNWPtdS8o4WRZcGmkvya",
          "EH91z8ktBCkKscpcPSkHDCkQ",
          "WOxdNSk+WQNcQW",
          "FG8wWOK",
          "WQxdUmo2p8kT",
          "FGHKq8klBCkmqsJcV8kgySkxha",
          "mwavtwa",
          "WQBdGmkLWOxcOJG",
          "WQBdQ8klBNm",
          "WRZdJSkJWOVcPcK",
          "WO7dN3LwWQ8",
          "WQddLSoccq",
          "dSkZucie",
          "W7JcP3ftWOu",
          "WQBcSv7cTNRdPmoPWQldV8k3W6qlWQRdMuqExSo6Ea",
          "WO8CWPpcTqbRCG",
          "WRRdSW9xWQW",
          "vrlcVSk0nNZcMmkqf2jpEIyR",
          "nSkOymoVqq",
          "WPlcNCkkzZK",
          "suqBWOlcSGxcGmoHWOWs",
          "WPNdGNy",
          "W7e/WOldQCovj2K",
          "WQRcHCkvFJK",
          "BYm+WP5cnGXgeG",
          "jSo8cmke",
          "WQ53j8o0W7K",
          "n8ooW65yqG",
          "WOFcUCoHWQldHa",
          "WRddPuOAj3/dPcWAnCkL",
          "WRxdPeuBpfNdL0W0",
          "tmk5WPtdMea",
          "lZZcU8kGrCkHt31b",
          "vmoxACo0vW",
          "nCoIW49kDSoEW6W",
          "W67cL2LWWPK",
          "W6FdQeddGSkH",
          "W5uIaX3dOW",
          "W51VW7icW6m",
          "6lw96l2154Qn5BoQ",
          "W7JdLKZdRCkc",
          "WOfmWOq",
          "W6y7WPJdJCoakxf6k8k3WPm",
          "Amosvmo2BghcMW",
          "pSkdFCoOv8k2cq",
          "jfu6srm",
          "WPpcQSkmWRGM",
          "WO/cIvVcI24",
          "WPZcLJZdJ8kf",
          "o1ZdGSklAG",
          "WQ3cPItdHCkd",
          "AqeqWP5sWPlcIZiT",
          "WPysW7byeG",
          "D8o9dSkXp8o2FtKYW7ekWQpdNmo4jSkWWOXBDSkxwCkdW7C",
          "oh5JWRrH",
          "WOmXW7v7aa",
          "vCk/WRFdSuXqCWFdVHWHxgCtEe/cL8kBgW",
          "W6eOWPpdGCovj0fxpmk/WPDzuW",
          "BCowlCkxnq",
          "vJtcG3ihW7pdVZ9+W5jSWPTyW4LilCk7",
          "WOfbWQCsaG",
          "6kYG5l6/55EmW5yFumk1uCo1qCo9D8oGWQySWOFMNPdMLRJNIlRLUyFNOjtKVRddJWaGdCoUWRno6kYt6zAL772H5OUZ5lYZ55wi5Rsl6kwW5zQK6is65BMG5OUH5Bof5O6x6zor",
          "WPNdIM5xWQVcL8oFW65DDMlcK8khB8oH",
          "pSo2eCkuWQBcU8og",
          "WPldPgfxWPG",
          "W4JcVCo+WPi",
          "BmorW6eSpaDzWP8C",
          "iCoYgCkaWOdcOmovqNW",
          "cSkiysK",
          "WPW5exC",
          "W6nQdmkkhW",
          "aI/cV2rj",
          "WR3dGCk9WOpcOJy",
          "WRVdH8k+WPS",
          "EGfXDCkurmkivZi",
          "oH5uW5xcVW",
          "WOW5d2izWRtdNa",
          "WOdcImodWRy",
          "oMb+WOH5jWjZkCknfJddUru",
          "W70GmHBdQq",
          "hCkDW7aKmCoJl8oG",
          "hSkhW7Om",
          "5BEZ6lwp6l+354Uu5AsGdG",
          "WRWqW5VcRCoV",
          "gSkTwCoRqa",
          "aHTVW4pcVq",
          "d8kaW6eplmoH",
          "WOCQW6jYeCobnSkX",
          "WQJcRuNcHxFdPSoS",
          "WQZdHSkIWPZcRtZcMW",
          "WRVdR183oNtdRG",
          "oMj6WRjKkcHRh8kiha",
          "6k+U6l++5yw16lE16lYG54Mp5BoF55QG56Au5PA7",
          "WRaEmgm3",
          "W4pcH0f4WO4MoSkDcc0k",
          "jSoRbCkv",
          "pSo5W5vFDmolW7qZC8odWOW",
          "WO/dUK4BkG",
          "l3pdKCkV",
          "eIhcKmk/yq",
          "WRZdVNraWQG",
          "WPfSp8o8W44BW4FcMSkAzM0",
          "aSkzW5Oofa",
          "W43dONZdOSks",
          "EcXhcmk/",
          "dxFdGSknD8oNWPJdJ8k8uI96cWNdJaldM8otWOWhtNi",
          "WQJdR0yoiNddT2q",
          "WQRdNmoskCk7W5yYyqbNcSoWW79f",
          "WRpcSupcHa",
          "FqX+A8kgy8kuzttcRSkL",
          "WQtdL8oicCkLW6C6FbO",
          "cSkdCci7s8ovsSkz",
          "DqSeWPK",
          "eCkNW7JcPcq",
          "gafEW47cHsu",
          "WPW6o38J",
          "WPyoW73cPCoAWPLvWQbqWPJcLmo6WRCgWONcVmo3nupcTa",
          "mgyBx3O",
          "WPBcMwVcPK0",
          "WRDPWPuXja",
          "wCk1u1T8W41aaa",
          "FqrJDSklACky",
          "WPO2W6HZ",
          "vSopE8o1rW",
          "AGv/Cq",
          "sCkuux1g",
          "rSkIWRFdJ1Xu",
          "WRldUab5WP1lvmo7WROVD2OEhW",
          "WPhcNCkcvtO",
          "W6FdNmkPWRJcONlcS3e",
          "W73dMCkJWQtcMgpcONddGW",
          "EXSjWPfjWPZcLIeTWPFcM8o5WRBcICkryLG",
          "W5H1W7GCW6ZcNLm",
          "c8kdW7Oumq",
          "i8oUW5fvBmoA",
          "j8oRmSkCW5xcH23cQclcG8k2",
          "CSovW6W5",
          "WO7cJ8kjFa",
          "W7/dMSkEWPZcUG",
          "yZu7bCoS",
          "f8kBzGy5",
          "WR3dUf8oiNddUMqkcSkXWRFdLe8UWO1Mj3tdK8k/cX0mmSo7W7i",
          "BmooW7eWfG",
          "drvbW4/cJW",
          "W4tcGuvX",
          "WOq1eNubWR0",
          "l2RdOmkfqq",
          "jSoXfCkE",
          "WQhcR1W",
          "pCkIqMWLqSoExq",
          "Cse5imoRpXJdQCoCW5BcLXK",
          "be8P",
          "smomkCkohW",
          "W4ddOvxdGSko",
          "EGSrWRHwWPRcIseMWO3cNmoSWPRcGa",
          "n8o8nmkrW6e",
          "WPS6W7tcS8owWPeyWRaqWPBcNG",
          "WORcK8ksEZ8z",
          "WPhcJmodWQldTq",
          "CYmSjmoXpGVdRCouW4pcLG",
          "FaPiWO1BWORcLYfLWPRcSCo7WQFcHCkDyKLF",
          "gMtdMSkiFG",
          "BSowjCkRF8kljCoZA8o5",
          "EmokW6eAeq",
          "WQDBfCoBW5C",
          "wZ4RWPHU",
          "W7JdM8kUWRhcUepcPg4",
          "WRJdN8kFuhK",
          "iSkOW7CZoW",
          "fmkGqruQ",
          "W6JdNSkVWQW",
          "W5/cNmoKWPq5",
          "W4avWPtcTW9JC8kjW44coW",
          "ArCvWPG",
          "nSoWa8kaWQpcTmoy",
          "W67cOmosWPCr",
          "gSkGW4BcGIPNhqGb",
          "5yMx6lYO5lQ4W7NcKCor",
          "s8kUu39CW5nrhey",
          "WO1yW4m",
          "WPtdMK8Daa",
          "kIpcHf5L",
          "WOhcSw7cN2q",
          "WRldOwDCWOG",
          "W5ldPLBdMCkuW4tcQZNcSvNcHmkixW/cKW",
          "WQ/cGNRcUMq",
          "wYPMiSk3WP3cMCkYWP7dPCkHW5WmamoL",
          "WOpcJSohWRxdUa",
          "i8oZcmkeW6e",
          "jmoWiSke",
          "pJJcTSkP",
          "W6G4iHhdSG",
          "WOnAWPiAgKtcK8kPWQeNxqLD",
          "vXHLqSkm",
          "mSo6pSkjW7xcGe7cUspcHmkJ",
          "W67cU8olWOWq",
          "WPhcJ8oiWRG",
          "WQpdRKH/WOPadCoCWRaNyN4BbCkzWQq",
          "W4/cH018WPq3hSkfbc8bdCkY",
          "FqX+A8kgy8kuCI/cUmkTECkYhq",
          "W6yZWOxdKmoni30",
          "W5bZW6Gh",
          "WOhcHCogWQtdVCkW",
          "s8kXq2n2",
          "5B2u5BQ65O2h5lQn5yUJ6l+X5yA56zAvW4u",
          "Eb9Kk8klACkyqttdPSk2DmkQgCkmW5K",
          "WPRcJSocWQtdRmkmFmk1WPC",
          "yWVcS8koba",
          "WO3cImkkWOer",
          "cZ7cMhzLW7xdRJLL",
          "nSktW73cLc8",
          "W5NcUvjfWPq",
          "hGxcQSkgsq",
          "e1HMWODf",
          "WONdTCk5EW",
          "WRVdM8kOWOdcPa",
          "5PsJ6lY85BcZ5BMh",
          "qGFcQCk1mG",
          "fXZcV2np",
          "Can+y8kvqmk1AqO",
          "nsXRW5hcHq",
          "EtyL",
          "W4/cVCoJWO0",
          "gsxcGwneW6tdMsnJW5DM",
          "WOC6W6FcO8onWP4wW6K",
          "DGNcImkHlW",
          "r8k5WRRdGK0",
          "W6P3h8kbbaFdTq",
          "W5xdOfddHa",
          "WRxcRf7cIgRdOa",
          "6k+L6l+a5ys56lAY6l2y54ID5Aw855Ib56wV5PEF",
          "dmo0dKzBW5Xck00",
          "l8oXkmkyW4tcP3tcGaO",
          "WRJcKG/dJ8kV",
          "mJJcPSk5B8kQ",
          "W49OW7iaW6u",
          "W70xbt3dRa",
          "WQ88W7NcOSoj",
          "wttcJ8olk8k+WQddVCkzurf6",
          "WPxcMdddPmkY",
          "W5moiIddKW",
          "W48pWOFcOqnJymoWW4uajG",
          "Aq0gWO9T",
          "xchcHCkibW",
          "aKhdSmkhuW",
          "WOBdQSkpDM7cSMNcN8ooeJa",
          "BHOkWO1QWO3cIZqPWP7cV8oHWRRcI8kA",
          "W5xcTSoOWOmNgWasuG",
          "WR7dHSk1WONcRMFcKhtcVmoAwCkIWRu9Amo8",
          "W5FdISkEWP/cSG",
          "WP3cJ8oyWQJdVCkH",
          "khD+WP5+kqy",
          "WQVdG8kWWP/cSHhcI2BcVa",
          "oCk9W5BcQW",
          "WRJdTSktWRJcJG",
          "W6NdICokdCkUW5yT",
        ].concat(
          (function () {
            return [
              "h8o5imkKW5K",
              "ohFdTCk7sG",
              "W6W2A8kHWQHpWOdcUmkiF2arW48",
              "WPe3W5VcSmoo",
              "pZ/cOmk/yCkQ",
              "EqKYsY9MWPqcDciCf3DPWQ3cIrjXW6PIsSkfWO7cVsFdNW",
              "WQNdIYTnWOe",
              "BCoBW6y7fG",
              "WQBdOXz/WPrewq",
              "WRTBnSoxW74",
              "W7a/WOxdJ8onnge",
              "vqfJkmkd",
              "WRhdOqX/WRflvmonWRa",
              "nKKKvG",
              "WRFdN8kkzN8",
              "WPG8hwS",
              "WQZdPqTQ",
              "WQBdLqG9W4bYE8ojqx4acSkWW6q+W5ZdLCoJpmkAWPCwdebOW5TyW7dcLLhcOwlcLHOPm8oOd8k4W6XVW77dOZJcTmoXBvq7WP7cNgmqEIpcKbTdy8obW6G1WP8o",
              "hCkjEsqK",
              "W4/cRmoPWPyfitSVF8kVWPffASoxWPm",
              "hWtcI8k9vq",
              "ymoormk+EehcNIRdTCk7BCkbW5VdMrG",
              "kfpdPSkdmq",
              "5lQz5l+m5A605lQW5lIc5OMp5PYu5lQR5RwV77Yn56E55QY35zwh55w3776f",
              "WQJdMmoPdSkZ",
              "WOhdSmo1imkM",
              "vrqubSoP",
              "W403WOZdTmoq",
              "WOTnWO4",
              "W5hdGmonWRtdQSkRwmkuWRRdJmoFvwjusfpcKwVdGXRdMmk9C8kEWOSOWQLrrmonW7yrWPj+dSo3pr0XW6q8WPRdQCoqge05W5JdVfz2CWGyW5tcIMFdHSoZodyWW5tcQSom",
              "zrJcLSk4hq",
              "uYjMja",
              "W7ymWR7cMsi",
              "hrlcV8kYxW",
              "WPtdHwnwWR/cMmopW4i",
              "WPNdSmk4zNhdRx7dGmoCgYi",
              "xmkSsw5XW4PapeZdM8kgl8kzwdJcMYhdTaL4WQa",
              "amoQmSk/W6W",
              "WRjXn8o9W7ikW5FcM8kwENC",
              "iCoLp8ksW4i",
              "WP7dH2fjWRNcSmodW4jm",
              "cmkRzaqP",
              "W7qTfrFdQG",
              "W7/cM2L8WRG",
              "hCkeyZ4Tq8ooBmkDcvW",
              "vSoWeSkY",
              "WPaWW6hcKSotWPOsW7GCWO3cPmo3WO4o",
              "WPq0W7VcP8otWP4g",
              "W6O3fZJdKa",
              "WOJdHwrFWQZcLCoeW5rC",
              "WPG8hwSxWRtdHSk/lsDhWRe",
              "W4bAh8klhW",
              "W5ldJ8kJCZuBWQJcMa",
              "6lwF6lYY54MV5BcJ",
              "W6xcOmosWQ0W",
              "FSoDW6SYaq",
              "c8kdFq",
              "WPhcJ8kdyb0BWPZcJH0",
              "W73dL8k+WP3cO3pcUW",
              "WRXNlq",
              "h1ZdS8kfpW",
              "W7a/WPVdJ8oxjW",
              "W4JcQSoNWOGMpZuRE8kqW5GeC8oaW5q",
              "nmkKW73cPXe",
              "lxRdMmk0dq",
              "aCo8W7RcMbGjxd3dIcqgDG",
              "fr/cUSkgxG",
              "WQhcOCkiWOm5",
              "hXhcNCkyAW",
              "lNddVSk3sW",
              "WQnLWPK1na",
              "WP8rW6zgpG",
              "WO/dHhrBWR7cMq",
              "5BAV6k2r57286lwO6l+154Qc5BgdWOC",
              "WROMW5fYaa",
              "m8kuDsuPzmouxSkB",
              "d3tdKSkqaq",
              "rslcTCk4aa",
              "W4OQabtdIW",
              "WOFcKmkhys8WWPdcKX0",
              "WQpcPCkCWOiFv8kPsSo9sSkM",
              "W58FWOhcMHjOEq",
              "W493W6iCW4NcKv4tW4S",
              "WP8RW5zllq",
              "W5RcUCoQWPuW",
              "W4ldVvFdNCkHW5JcSa",
              "WQtcR0xcMNVdTSoZ",
              "6k2P6l+s5ysJ6lAg6l2g54IX5Bcq55Q456EV5PEM",
              "W4FcMSkaDdOAWP8",
              "WQSxW7f6dq",
              "tmkGsxS",
              "mKCKta",
              "WPSMnKm/",
              "WQhcTKBcHw3dPSo1WQRdU8kY",
              "WQ/dP8k5WOFcJq",
              "l3nTWPLRiq4",
              "amoHjmkbWOS",
              "khPLWQa",
              "WOaRW7v3b8oa",
              "WQhdKmoibW",
              "ddRcVwLDW6xdQaHRW4HN",
              "W6RdM8k5WQtcU3FcRW",
              "5BwS6kAI6zwh",
              "W5dcT8oNWOi8ptm",
              "W5GFWO3cPYvIESoqW4KdnW",
              "W4/cPJdcTCo+W4tcMa",
              "WQdcM8kjvcK",
              "nx1+WR5Pkq",
              "WQZdNCockCkHW5yXCcj6o8o9W5npeYC",
              "iSo+mSkC",
              "BmouCSovqq",
              "fXfdW53cNIa",
              "ACovW6qPhHDoWOuscmkgW60",
              "pZJcVSk/FG",
              "qmkLWQBdGa",
              "DCozq8oN",
              "qmkIWRBdJubuCW4",
              "WRa4W5VcGmo8",
              "W45zW4CKW7C",
              "lCkZW57cPYm",
              "WP7dUmoEcSkt",
              "pCoKW5S",
              "WQXVomocW58",
              "wb3cS8k1iNpcImkS",
              "WP/cQdNdTG",
              "cMaouqe",
              "bwVdMmkyACosWOtdKSk6",
              "WO/dQmkzWQVcTW",
              "W4jHb8kNbW",
              "FSokW7G5hrzUWOuAcSkf",
              "W5hdG1RdQmkx",
              "WOxcGCoaWRtdUW",
              "WP8XW6rShCo2nSkUemobW7LisW",
              "AqyaWPm",
              "W5RcRCoQWOOMmcy6E8kMWRvDzSovWPJcVeW",
              "6kAD6Akd5PYG5BoM57UG",
              "WONdV8kyW4ZcTdpcG2pcQCowvSkRWRy/AG",
              "pH9gW5pcVG",
              "WRBcSSkqWQKVu8kUtSohtCk8rSo2WQ4",
              "rqhcSCk3jhhcGSkTcG",
              "kJBcVSkLAq",
              "WQDQWRWlha",
              "CI1BdCkt",
              "W4faeSkwdG",
              "WRJdO1GoiNddUG",
              "oJVcPa",
              "WO3cSIlcRmkMWPhdLCkwW6ddQ8opWOFcNmoR",
              "nSo7omk3WOq",
              "gHaaW4RcMc3dOSoAWR0pW5ug",
              "WRZdGmkH",
              "WPhcHSkLsIG",
              "W5ylnXFdSq",
              "iSo2nCknW5RcJLK",
              "lYpcVCkGxmk9vh9pzHKHAdddQG",
              "WOdcI8ofWRhdL8kQxmkkWRq",
              "mCo1eCkdWRZcMCoiq2C",
              "iCo8bmk5WRVcSmom",
              "WOKzW5xPUyhPU7NMKQdMLkRLM4ZcJeGGWR4yuSkkdePPtmoZDXbgmXSlW5NcLCkLB34TCCke",
              "W54FWPJcVbbO",
              "W641WPFdHa",
              "jKO3usOuW7Dria",
              "CbnFgCku",
              "lwldKmkLgW",
              "WQxdTSkvWRVcPa",
              "nSkKrCo3vW",
              "qSkhEcGTqSkAs8kgbWtdVG",
              "uCoQhmkRi8oIDY9/",
              "WROhW7tcS8o2",
              "W6tdUCotW4yrDSkFASo9qq",
              "W5OGWOdcTWS",
              "WODnWOmYgKtcUW",
              "vCkQt3X2W4TkgeW",
              "W6y7WPJdJCoakxfKpmk8WPnvs8kIWQS",
              "yCoYfCklkG",
              "eWbaW5y",
              "WO82W7vUcmoekSkNb8oYW6fsxNJdJCo+WRdcU8oclxldPmoLW6KYf8k3",
              "5P2X5OML5yQe5B+45BI95O635lI95AYQ5l2r772O6k+05Qgo5PYx5O2w5lIP5PMr5zcr5Q+o56kT5yIQ5Asu5yYn",
              "td1chSkC",
              "cLW8xvyZW4bnW4ZcThZdOq",
              "jrT5ySkcz8obvZtcQmo5oq",
              "fmobW5H/Da",
              "WQVdNCk0WO3cTtJcP3NcRCosx8kKWQa",
              "WOjhWOuFc1pcLCkQWQGLsG",
              "kxb9WPTz",
              "WOZdIeOZna",
              "W7yZWPVdHq",
              "WOJcOSkiWPCYuW",
              "lZZcU8kGq8k6t31b",
              "if3NP4i",
              "aZxcVSkXySkK",
              "mxCZqW4",
              "W6/dGSkJW7VcPxpcPw3dGgxdOxxcHmkHighcQX3dPtlcJSkd",
              "WQpcM8kZwJO",
              "WPWHW6XXeSoa",
              "n1hdJSkYkG",
              "WQVcReNcGG",
              "WOVdNdrvWPa",
              "pSkOqSoUwq",
              "aNy9BuO",
              "5B285BMZ5yU26l2F5OMj5yUh776s5ywt",
              "W692dSkqgq",
              "5BsA6l6o5O+z5OQh5Bc66k2R5AAI",
              "W5JcNfXXWOu",
              "W5tcMCowWRuV",
              "W5f5W7GFW6hcMe8",
              "a2VdLCkrCSoLWOO",
              "xmoSkCkaoG",
              "W7tdMSkmWRdcUa",
              "EZ0/lCoQpI3dTG",
              "mCoXaSkFWQlcSa",
              "gKuWtg0JW6rtW4i",
              "WP7dJeX4WOC",
              "WRODf1mr",
              "WPFcLmkjzq",
              "vSk1EvvR",
              "s8kGtKzNW4ni",
              "WO7dOCk/W55Gfb81xmkGWPu",
              "5y6M5lMQu+InSEIbTEA2MUILREwAVoABVEs5I+AuNoApLEE+M+MGRUAlHEwYMo+9M+IUUoEuJEEYI+E5NEobRUAvMoE6LUAlTEwWK+odM+AkHUoaQEwNQEwZTEwpJUwqKoodKW",
              "pCo/oSkvWRO",
              "WRtdPqL6WPva",
              "hMddL8kzyG",
              "WPpdHN8Xdq",
              "pKddMSkhAq",
              "WRaGnahcRavlseNdV8kVW4JdT1e4W4LihfZdK8kubfaAWP3dKCkPWRVcG8oNW4K2WPlcUmkoWRqBodlcGG",
              "nCk9W4BcUYvJ",
              "WR3dH8kfWO3cRa",
              "oxtdKmk4",
              "W60OWP/dHCopnMvpmmk9WPW",
              "nCo8bmk1WQpcSmomvx0UW5T2fd4",
              "BCkNWPtdRwq",
              "WOVcSCoRWRhdUW",
              "eGvyW7BcIq",
              "ohtdMmkUgL/dQ8kxWRWczCk1W5ldPSk+hvZdISkXwmkQDCkVWRZcL8k4W5yIlchdN8kxgmkLq27dHCoyW5dcJCoZW7ldUL/dMSkSW5xcVZ3cVd8PWRlcSSkvsc9VW7LcWQC+ECokWOpdR0zYWR1QWRaZW7ZcR8kFga",
              "W7lcGCoQWQC0",
              "feqbCcK",
              "qHZcOSkT",
              "WR/cHCo8W63dPcpdO3hdLwRdOchcHa",
              "WRBdOWHQ",
              "WP3dVmkXBgJcPW",
              "WOxcISkEWRO/",
              "WRFcSuxcHg7dSq",
              "WOlcRYldQmkPWPu",
              "ptXmW5xcGG",
              "WPhdS1msdW",
              "W4/cS8oVWPyAjIaTCq",
              "bL4Tvu04",
              "W60KmJZdTrnd",
              "WO0IdN0h",
              "5BAP6k6L57+A6lsY6l6V54II5AE/WPq",
              "5BsW6kY057Yl6lE86lY/54MI5BcEWP8",
              "WPVcSrRdMmkZ",
              "jmoCW4Tnya",
              "WOiRW6y",
              "usr8jSk1WPm",
              "lCkWAsOm",
              "WPjxjmo7W5u",
              "ECowW6CZaq",
              "cSoDfCkFW4y",
              "W4qpWPtcPanKDSowW4mAmmo7aG",
              "WRfSoq",
              "6iww5A2c5lUpW4H7Fq",
              "xGHKvCk3",
              "CduyamoX",
              "W73dMSkLWQm",
              "W6pdM8kK",
              "xCkJWQddGL1vEbK",
              "bdxcTSkAtW",
              "vSoSbmkPnq",
              "gx43C2a",
              "zbOXWRHq",
              "vCkvx1H5",
              "ohDRWQDH",
              "WQNdPeCrlxO",
              "WPZdMxqxWQBcK8ojW5PDFc7cNmkeBSoG",
              "W495W78LW7tcMKC",
              "W61kW5OdW5i",
              "g8oSoSk9WQu",
              "jmo4hmkfWQO",
              "W4HUW6OcW7pcMuutW4K",
              "WQ83W5r7fG",
              "xCk3sgbH",
              "xHbGpCkZWPddHSoqW5NdQSkYW4OqcCoGWP/dPLBcOmkJ",
              "EYOpWOHn",
              "nCkkySoSvG",
              "WPBdRZzvWPO",
              "WR3dRK87ohtdRxu0m8kUWRBdLKGLWRS",
              "WRBdQWjbWPLirq",
              "WR/dSKmwiG",
              "WP/cTc/dRCkV",
              "ohFdLCkYgYVcQSozWR8",
              "WPK6W7VcSG",
              "uYrPk8k/WPJcI8oaWPNdPmk4",
              "W490W6qB",
              "5BsE6k2+57Y46lwY6lYn54Q35AAyW5m",
              "b8o5W4LkxG",
              "mZNcSCk8zCkSua",
              "q8oTeCkPi8oNAJH3W68",
              "f0NdM8kLgq",
              "W7VcV8o0WQud",
              "BdPNa8kc",
              "WPpdHg5F",
              "W5hdOfZdN8kHW5JcSa3cTvJcHmkjwHq",
              "vCk/WRFdSuXqCWFdVHWHxh4kAKxcNmkdbW",
              "amoLp8kwW5m",
              "5B675BIp5PAg5O+o5QkD5B2n5lIj5Q2y56c3W6G",
              "hvW4uLeWW79tW4a",
              "AbH1DmkEw8kescpcQmkWDmkSoCkuW5a",
              "lspcQv5d",
              "hCokW7v0FG",
              "osFcLgC",
              "WRBcSSkqWOyWwCk+w8oQ",
              "W6jXdCkvaqJdQW",
              "c386F8oMW4/cP8kgWRxdUCkRW5y",
              "C8k7WRVdUwq",
              "W5OBWPNcPGm",
              "WROSW73cGSoz",
              "cmoIWQFdH14pf0RcV1D0iZfAkXRdMSktfWpdUbT1W57dUmo2",
              "W6xcJSosWPCs",
              "gY3cISkODa",
              "W7NcTSoSWPyq",
              "CGhcImkaea",
              "WRVdNNr4WPa",
              "As3cGCoYxbFcMmo9WRS0tG",
              "W6GOiHddRLLdtaK",
              "cCkkqCobua",
              "Fmo/hmkg",
              "lxnMWQjV",
              "W6dcQHvJWPLgrCoxWRaLCNOavSoE6kYH6l2A5yET56EJ5PsYerNcP8kjjSkBWOueW7hdJSk1nmkwCCowWP02WO1WW6TsnZP9WRCMf8oXW4xcH8kuWO9XxmkXcYldNxaFrCkvc8kIrXdcLer/z2SSkNfLm8oxWP0HWQNdL8oLW67cMmkYW57cS1hcISkEpSknl8kAW65FWQpdKmoGW7Wygs7cHSo6BCoQW7yVWPBdM8oVE8oKW54vghqhgmobWQhcTYy2y8kqfCkjWPxdKUwnVEA3G1VcObFcOCoLW7O6rLjAWRuaW6TiywzqFcvPlfNdGMjGBSoLtmomnMFdLCo6W5SRW4fWwd7cJSoKW5e/sZC+WPFcJstcHvawW5W0WOZcU8oWgmoUgNnIArLiW73cLvRcThhdJUEGRowVPmktW5lcRehdHJbRW6VdSZqPiftdKcCNk8olqMqKWPL6kSkKaSoRW4ZdLq4BqZiopW7cJSk2FwHOW5L2ixRdOCkZwG",
              "WQpdLSosbCk0W5y",
              "kfTYWOfC",
              "W7jHdSka",
              "WQGkW7BcTSomWOS+W60BWRJcKmoVWQ4gWONcP8o+iG",
              "mmoVWPfkAmoA",
              "WPHkWQqrgG",
              "kSkkW5C8dG",
              "mdJcTq",
              "xI9S",
              "wmkOWQ3dIvXz",
              "zGe4oCoN",
              "WPLCWQm+ba",
              "s8o3e8kG",
              "W53dOmoeW5z8gmoNhSk4gmkHrmoJW6e+W47dThWAdfHFW5TQvdhdM8kjcCoep1ddH35uzSkyWRRcUsmdW4JdSqClhmogFWuOmCkkeLPLnWRcPJBcGdZdSCoQfZpdRmooW5hcOW8UWOddSCkYWQ5HnbhdKHpdPmoeWQjvb8o7otqKwCkZfSoZmfhdILVdJ8oRWRDKW5hcR3NcNvFdUsrKoSkNWQNcPSoAW6tcS8omlKRcJvRdRxGSWQOrxIxcVNlcHHDRWPdcV8ounMnTlSodxCoJWPz+W7DuktZcMadcN8k9mZtdPSoane9NeHFcPSkzW6VcPNJcNs7dVu4zWP8iW51Elmk9WO9RACk2W4fRcCoGnCodCmouWQVdG0xcLa0PW4pdPJyawSkmW7DQwsVcR8opW6ThrSkFW74FoXf9ACo3jfxdGhldGsTAWRj3iSomtSoKW47cU8kaWPZdLmozmMf0WP3cMmkCW6ldN8k/W6/cUaCsa1xcSmkqESkyWOhdQ8kEgmkGnmoBWRZcVcVcUCkhfCkCqmobW7VcVCkCWO8OWRNcKLpcNeFdQwNdNCkGW6/cS0SpWOhcScFdVwldM0vGihZdT8oSW4tcTCkZW73cVHPqW7/dRSkcW7JcP30mq8kmySkEfSkqA8kxl8omzbtcQ8oOWQNcJSkBWRldVx9gmCoIW6xdLmkVBSkJW5KjlNrrWRtcO8kMr8k3E8k1WP3cKCkseMNdGYjOtGpcJ8oWWQLGrSodb8ohtmo/tu1FWO5uWODTxmohWOHnWQJdPuJcLCkRW7NcQvJcJYJdQCoxWRS/zmoHWQxcP8opdSoHaCohW6ldQmoSWODYW7JdRdZdLr7dH8khpJRcNc9WWQhdICoXqd/dGmkqoGuWW7W6sw7cGs96WPxcVcK6vGldUaVdNgJcMmoyW53cTZmAtCoSpMBcICoQWOFcGbHWWQOXBhRcT8oCWPnjWOP+W5VcVSknz8oEy8kJyCoRWPVdGaz0W7RdL8oTW4/cVSo2WRpcTGdcNKWtW6Wdke96jCo6A23dRLvzW7ZdP8oHef7dS8o2WQBdLXTVW5JdU8kOW4hdPSouW6BcTCoVpmkPqHNdNCoZW5hdSvZcR3ZdKaVcM8oTW4vKlGX0E8o4W70",
              "W6ddTxxdQSk+",
              "WPJcTIddJSkB",
              "W7eXWP/dKmoOlhbjnG",
              "gJnLW4lcIq",
              "vJtcG3ihW6pdTsv+W556WOGyW4vspCo7WPVdPuKSgmobW4e",
              "6lA26l+H54Ir5Asw",
              "W7KKmJddRrndwvpdOSkdW5BcK0e",
              "WO3cSIldNSkUWPhdGSkEW7pcRCowWRFcMCoVpCk5WRnHbCoi",
              "ntNcSCk8ECkRxNW",
              "WRKwW49YmW",
              "W6WUmXVdPq",
              "57cZ57MW6zEi6kYdW7T9",
              "6ygs5PUH5BQ0",
              "WRpcQCkxWOyWwCk+",
              "B8oslCkFjq",
              "mW8xWOKxWOZcGta8WPdcSmoYW77cJCkaAue",
              "k8oXW7jyEq",
              "hwTPoSkIWPNcNmkbWPRdSSoGW5mveCoKWOlcO0JdRCkrW4GkCuNcTCkfb8osWOddICkeWQ1tcxnAy8oQWQ3dOdBdSmo5W47dHarniulcRCkBzCoRW6WzWOtcOx7dUHPFcCokW5NdLmoxfCk3W4/dQq",
              "ub0ueSoo",
              "WRrnWQqHda",
              "keldSCk5ta",
              "AqfXF8kfACkctXtcQSkWFG",
              "EZ3cNmk/gq",
              "WQ7dLSoka8kL",
              "uINcGmkXgW",
              "ySoIjCk9ka",
              "WQVdO8kBWR7cJa",
              "kwVdGSkyAq",
              "rmk/WQBdSvPECqy",
              "ftZcNW",
              "cb9eW4RcOYBcU8oCWRS",
            ];
          })(),
        );
      })(),
    );
  })();
  _0x1a56 = function () {
    return _0x3330df;
  };
  return _0x1a56();
}
function injectModalStyles() {
  const _0x2f6fbe = _0x2b2717,
    _0x5a212a = { NwjDC: "style" },
    _0x38952c = document["createElement"](_0x5a212a["NwjDC"]);
  ((_0x38952c["textContent"] =
    "\n        .art-custom-modal {\n            position: fixed;\n            top: 0;\n            left: 0;\n            width: 100%;\n            height: 100%;\n            background: rgba(0, 0, 0, 0.7);\n            display: flex;\n            justify-content: center;\n            align-items: center;\n            z-index: 9999;\n            opacity: 0;\n            transition: opacity 0.2s;\n            font-family: sans-serif;\n        }\n        .art-custom-modal.show {\n            opacity: 1;\n        }\n        .art-custom-modal-content {\n            background: rgba(30, 30, 30, 0.95);\n            backdrop-filter: blur(10px);\n            padding: 24px;\n            border-radius: 12px;\n            width: 320px;\n            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);\n            text-align: center;\n            transform: scale(0.9);\n            transition: transform 0.2s;\n            border: 1px solid rgba(255, 255, 255, 0.1);\n        }\n        .art-custom-modal.show .art-custom-modal-content {\n            transform: scale(1);\n        }\n        .art-custom-modal h3 {\n            margin: 0 0 20px 0;\n            color: #fff;\n            font-size: 18px;\n            font-weight: 500;\n        }\n        .art-custom-modal input {\n            width: 100%;\n            padding: 12px;\n            background: #444;\n            border: 2px solid #555;\n            border-radius: 8px;\n            color: #fff;\n            font-size: 16px;\n            margin-bottom: 24px;\n            outline: none;\n            box-sizing: border-box;\n            transition: border-color 0.2s;\n        }\n        .art-custom-modal input:focus {\n            border-color: #00aaff;\n            background: #3a3a3a;\n        }\n        .art-custom-modal-btns {\n            display: flex;\n            justify-content: space-between;\n            gap: 12px;\n        }\n        .art-custom-modal-btn {\n            flex: 1;\n            padding: 10px 0;\n            border: none;\n            border-radius: 6px;\n            cursor: pointer;\n            font-size: 15px;\n            transition: all 0.2s;\n            font-weight: 500;\n        }\n        .art-custom-modal-btn.cancel {\n            background: #555;\n            color: #eee;\n        }\n        .art-custom-modal-btn.cancel:hover {\n            background: #666;\n        }\n        .art-custom-modal-btn.confirm {\n            background: #00aaff;\n            color: #fff;\n        }\n        .art-custom-modal-btn.confirm:hover {\n            background: #00aaff;\n        }\n    "),
    document["head"]["appendChild"](_0x38952c));
}
injectModalStyles();
function showInputModal(_0x282250, _0x1b0333, _0x3d1ef2) {
  const _0x279bcf = _0x2b2717,
    _0x47c483 = {
      KJcwP: function (_0x2933cd, _0x51faab) {
        return _0x2933cd !== _0x51faab;
      },
      iEOEY: function (_0x37e8c9, _0x2e9114) {
        return _0x37e8c9(_0x2e9114);
      },
      LRodq: function (_0x52e38c, _0x5bacdd) {
        return _0x52e38c === _0x5bacdd;
      },
      kpERR: "bottom",
      yoByW: function (_0x1e9827, _0x64efd8) {
        return _0x1e9827 || _0x64efd8;
      },
      ALGBG: function (_0x1cced0, _0x4847c3) {
        return _0x1cced0 || _0x4847c3;
      },
      oOamR: "show",
      WYtvq: function (_0x25f209, _0x16e411) {
        return _0x25f209 * _0x16e411;
      },
      sXomv: function (_0x5a5a0f, _0x5b9aa0) {
        return _0x5a5a0f(_0x5b9aa0);
      },
      yYYLI: function (_0x4591d3, _0x5b404f) {
        return _0x4591d3 >= _0x5b404f;
      },
      DGGDW: function (_0x1f9c50, _0x5e959e) {
        return _0x1f9c50 === _0x5e959e;
      },
      HJlPO: "PBaMz",
      aGHxc: "#ff4444",
      Ljuaw: function (_0x381235, _0x46cc2b, _0x2d09f2) {
        return _0x381235(_0x46cc2b, _0x2d09f2);
      },
      cGPuk: "Enter",
      tYMcZ: function (_0x206487) {
        return _0x206487();
      },
      tccrW: function (_0xffcb0e, _0x181ad5) {
        return _0xffcb0e === _0x181ad5;
      },
      CeNdg: "Escape",
      CyUGc: "div",
      uphaI: function (_0x1b6f44, _0x29be01) {
        return _0x1b6f44 !== _0x29be01;
      },
      MyxlA: "undefined",
      pBAnL: "hepwd",
      WBFag: ".cancel",
      oTaio: ".confirm",
    },
    _0xfd7a1e = document["createElement"](_0x47c483["CyUGc"]);
  ((_0xfd7a1e["className"] = "art-custom-modal"),
    (_0xfd7a1e["innerHTML"] =
      '\n        <div class="art-custom-modal-content">\n            <h3>' +
      _0x282250 +
      "</h3>\x0a\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20<input\x20type=\x22number\x22\x20value=\x22" +
      _0x1b0333 +
      '" placeholder="请输入秒数">\n            <div class="art-custom-modal-btns">\n                <button class="art-custom-modal-btn cancel">取消</button>\n                <button class="art-custom-modal-btn confirm">确定</button>\n            </div>\n        </div>\n    '),
    document["body"]["appendChild"](_0xfd7a1e));
  if (_0x47c483["uphaI"](typeof art, _0x47c483["MyxlA"]) && art && art["template"] && art["template"]["$player"])
    art["template"]["$player"]["appendChild"](_0xfd7a1e);
  else {
    if (_0x47c483["uphaI"](_0x47c483["pBAnL"], "dbHGK")) document["body"]["appendChild"](_0xfd7a1e);
    else {
      const _0x517619 = _0x57e803[0x0] !== _0x5ba4ff ? _0x3fd52a[0x0] : _0x5db0ef["time"],
        _0x55f1a2 = _0x530bec[0x1] !== _0x199c9e ? _0x505e8b[0x1] : _0x1dc62c["mode"],
        _0x746a5f = _0x47c483["KJcwP"](_0x3bfbe9[0x2], _0x162b8d) ? _0x5cedb7[0x2] : _0x11c460["color"],
        _0x109866 = _0x1d77ad[0x4] !== _0x34039f ? _0x2997ed[0x4] : _0x11a8be["text"];
      return {
        time: _0x47c483["iEOEY"](_0x113ab2, _0x517619) || 0x0,
        mode: _0x55f1a2 === "top" ? 0x1 : _0x47c483["LRodq"](_0x55f1a2, _0x47c483["kpERR"]) ? 0x2 : 0x0,
        color: _0x47c483["yoByW"](_0x746a5f, "#ffffff"),
        text: _0x47c483["ALGBG"](_0x109866, "")["trim"](),
        border: ![],
      };
    }
  }
  requestAnimationFrame(() => _0xfd7a1e["classList"]["add"]("show"));
  const _0x44436a = _0xfd7a1e["querySelector"]("input"),
    _0x4b8f13 = _0xfd7a1e["querySelector"](_0x47c483["WBFag"]),
    _0x44909c = _0xfd7a1e["querySelector"](_0x47c483["oTaio"]);
  (_0x44436a["focus"](), _0x44436a["select"]());
  const _0x2ad026 = () => {
    const _0x41be20 = _0x279bcf;
    (_0xfd7a1e["classList"]["remove"](_0x47c483["oOamR"]), setTimeout(() => _0xfd7a1e["remove"](), 0xc8));
  };
  _0x4b8f13["onclick"] = _0x2ad026;
  const _0x1fa05c = () => {
    const _0x3657b1 = _0x279bcf,
      _0x129c07 = {
        hDoSF: function (_0x27e113, _0x1b357e) {
          return _0x27e113(_0x1b357e);
        },
        BNHSQ: "#FFFFFF",
        fPioN: function (_0x5c79a7, _0x140307) {
          const _0x4969bb = _0x3657b1;
          return _0x47c483["WYtvq"](_0x5c79a7, _0x140307);
        },
      },
      _0x8f39be = _0x47c483["sXomv"](parseInt, _0x44436a["value"]);
    !_0x47c483["iEOEY"](isNaN, _0x8f39be) && _0x47c483["yYYLI"](_0x8f39be, 0x0)
      ? (_0x3d1ef2(_0x8f39be), _0x2ad026())
      : _0x47c483["DGGDW"](_0x47c483["HJlPO"], _0x47c483["HJlPO"])
        ? ((_0x44436a["style"]["borderColor"] = _0x47c483["aGHxc"]),
          (_0x44436a["style"]["transform"] = "translateX(5px)"),
          _0x47c483["Ljuaw"](setTimeout, () => (_0x44436a["style"]["transform"] = "translateX(-5px)"), 0x32),
          _0x47c483["Ljuaw"](setTimeout, () => (_0x44436a["style"]["transform"] = "none"), 0x64))
        : _0x37cd5b["push"](
            _0x129c07["hDoSF"](_0x3144be, {
              danmuku: [],
              speed: 0xa,
              opacity: _0x30876b["danmakuOpacity"],
              fontSize: _0x5e7bb9["danmakuFontSize"],
              color: _0x129c07["BNHSQ"],
              mode: 0x0,
              margin: [0xa, _0x129c07["fPioN"](0x1 - _0x682a9b["danmakuArea"], 0x64) + "%"],
              antiShield: !![],
              synchronousPlayback: ![],
              visible: _0xe121e0["danmakuVisible"],
            }),
          );
  };
  ((_0x44909c["onclick"] = _0x1fa05c),
    (_0x44436a["onkeydown"] = (_0x5f258a) => {
      const _0x4886d9 = _0x279bcf;
      if (_0x47c483["DGGDW"](_0x5f258a["key"], _0x47c483["cGPuk"])) _0x47c483["tYMcZ"](_0x1fa05c);
      if (_0x47c483["tccrW"](_0x5f258a["key"], _0x47c483["CeNdg"])) _0x2ad026();
    }),
    (_0xfd7a1e["onclick"] = (_0x4d2a7b) => {
      const _0x8c541f = _0x279bcf;
      if (_0x47c483["DGGDW"](_0x4d2a7b["target"], _0xfd7a1e)) _0x47c483["tYMcZ"](_0x2ad026);
    }));
}
function updateSettingTooltip(_0x20ae66, _0x238745) {
  const _0x18efca = _0x2b2717,
    _0x4bd953 = { OXWVB: ".art-setting-item", MRadI: ".art-setting-tooltip", VRnuN: "BVusW" },
    _0x50f853 = document["querySelectorAll"](_0x4bd953["OXWVB"]);
  for (let _0x581e8c of _0x50f853) {
    if (_0x581e8c["textContent"]["includes"](_0x20ae66)) {
      const _0x5f273f = _0x581e8c["querySelector"](_0x4bd953["MRadI"]);
      _0x5f273f &&
        (_0x4bd953["VRnuN"] === "BVusW"
          ? (_0x5f273f["innerText"] = _0x238745)
          : (_0x1850fc =
              '<img src="' + _0x30ba0b["content"] + "\x22\x20style=\x22max-width:100%;\x20max-height:100%\x22>"));
      break;
    }
  }
}
function initPlayer(_0x78f13e, _0x5d87cf) {
  const _0x564681 = _0x2b2717,
    _0x138822 = {
      FHaoh: function (_0x27bab8, _0x1ab500) {
        return _0x27bab8 === _0x1ab500;
      },
      qhTHm: "CFuoc",
      gwYDD: function (_0x4bc169, _0x5f5a4c) {
        return _0x4bc169 + _0x5f5a4c;
      },
      MyhUf: function (_0x418f7a, _0x372b4f, _0xa8877d) {
        return _0x418f7a(_0x372b4f, _0xa8877d);
      },
      OKlVl: "跳过片头",
      DTxmf: function (_0xa6fe47, _0x4140d1) {
        return _0xa6fe47 + _0x4140d1;
      },
      hAPSz: "custom",
      oINee: "art_skip_intro",
      KBGcU: "NYlAa",
      TkFaJ: "art_skip_outro",
      ytTEj: function (_0x5ace16, _0x28cdc2) {
        return _0x5ace16 === _0x28cdc2;
      },
      TYrfr: function (_0x286274, _0x5484bf) {
        return _0x286274 + _0x5484bf;
      },
      mCydX: function (_0x515aac, _0xdf8a81, _0x281069, _0x22acb6) {
        return _0x515aac(_0xdf8a81, _0x281069, _0x22acb6);
      },
      AUtzb: "请输入跳过片尾的秒数",
      ovFFV: function (_0x411c58, _0x33045c) {
        return _0x411c58 !== _0x33045c;
      },
      eAqpD: "application/vnd.apple.mpegurl",
      TbPld: "flv",
      xDjzY: "loading-box",
      GzXxx: "none",
      sHRBY: "loading",
      RJzLc: function (_0x3dd512) {
        return _0x3dd512();
      },
      FBanr: "#ff4444",
      uadGf: function (_0x16509d, _0x106d21, _0x28e27c) {
        return _0x16509d(_0x106d21, _0x28e27c);
      },
      WAbJJ: function (_0x1135f0, _0x3ed7a3) {
        return _0x1135f0 === _0x3ed7a3;
      },
      HPdcN: "YQmTc",
      RxTqD: function (_0x534e00, _0xc7d746) {
        return _0x534e00(_0xc7d746);
      },
      cGdHE: function (_0x272521, _0x442e0d) {
        return _0x272521 === _0x442e0d;
      },
      FneVe: "hsItU",
      EkkiT: function (_0x1938cd) {
        return _0x1938cd();
      },
      Nysle: function (_0x562362, _0x2713b2) {
        return _0x562362 !== _0x2713b2;
      },
      GetSP: function (_0x33fd92, _0x5cc942) {
        return _0x33fd92 === _0x5cc942;
      },
      pVjNO: "CwBiI",
      cVCHm: function (_0x4b3ad5, _0x28b743) {
        return _0x4b3ad5 !== _0x28b743;
      },
      AxiHf: "UvXXi",
      aslkJ: function (_0x2f35dc, _0x2b00c9) {
        return _0x2f35dc !== _0x2b00c9;
      },
      MfSBE: "gMGlo",
      QZAOS: "portrait",
      uGBet: "landscape",
      wbuoi: "Rotation\x20fallback",
      SdzpF: "恢复默认",
      KVsuL: "style",
      pjUCd: "弹幕插件加载出错:",
      hKdrt: "show",
      BRxVE: function (_0x31c682, _0x123876, _0x12beaa) {
        return _0x31c682(_0x123876, _0x12beaa);
      },
      tcpuH: ".icon-unlock",
      KBljJ: ".icon-lock",
      ovOuW: function (_0x5b950b, _0x437e7f) {
        return _0x5b950b !== _0x437e7f;
      },
      YxTKe: "VGIhq",
      NXFko: "block",
      qcrlW: "已解锁",
      ofJeu: "KYhDE",
      GgUHf: "RvuXO",
      IfnVZ: "屏幕已锁定",
      fbNgq: function (_0x39a3cf, _0x4d1deb) {
        return _0x39a3cf / _0x4d1deb;
      },
      iquLc: function (_0x3211aa, _0x311784) {
        return _0x3211aa < _0x311784;
      },
      vZudm: function (_0x1a3cce, _0x52a67f) {
        return _0x1a3cce - _0x52a67f;
      },
      GaiAs: "gHhkL",
      pYrXj: "gyCMW",
      cxhhl: "ArtPlayer",
      ijwJq: 'a[href*="artplayer"]',
      XFVea: "kPTXb",
      yQfZx: "CSYmY",
      fTeyL: "未选择设备或投屏不可用",
      VnCre: "已投屏到设备",
      ZxLZK: "JteRy",
      QQJCF: "NNbxn",
      wrqbT: "未选择设备或已取消",
      RMkAd: "投屏失败，请检查设备",
      RKgza: "已连接投屏设备",
      uLzXt: "仅供学习与技术交流，禁止商用！",
      LczOr: "视频未就绪",
      TrCFQ: "function",
      AqvNc: "RcMjE",
      pPnOB: "BAwgx",
      pjlkz: "tEpLb",
      avdCj: function (_0x399814, _0x47efc9) {
        return _0x399814 === _0x47efc9;
      },
      NuuDk: "qfgDs",
      EnjpE: "mTTKO",
      RElzr: "application/x-mpegURL",
      GGHGv: function (_0x43d665, _0x3193e9) {
        return _0x43d665(_0x3193e9);
      },
      Fzyke: "prlKT",
      xQGpe: "huaweibrowser",
      dUuul: "honor",
      mhBFU: "华为/荣耀浏览器暂不支持网页投屏，请用系统「无线投屏」或「多屏协同」",
      uhTam: "MOdUR",
      UUUXv: ".art-contextmenu-item",
      zhFdo: ".art-contextmenu-version",
      uXVkZ: function (_0x5e29ca, _0x495ed4, _0x384f55) {
        return _0x5e29ca(_0x495ed4, _0x384f55);
      },
      sbbBE: "art-locked-mode",
      tRdxx: "art_playback_rate",
      OTlGQ: "art_volume",
      IZsry: "art_muted",
      xSAuU: "Restored playback rate:",
      jmRaT: function (_0x1b7fcd, _0x3c7a52) {
        return _0x1b7fcd > _0x3c7a52;
      },
      HNSay: function (_0x115c42, _0x3fd3a3) {
        return _0x115c42 < _0x3fd3a3;
      },
      xbSjt: function (_0x47c2c1, _0x506749) {
        return _0x47c2c1 > _0x506749;
      },
      UrQZJ: "WsKfS",
      JcUmb: "Danmaku\x20Show",
      jmtuC: "Danmaku Hide",
      TRYNe: "false",
      kiIGJ: function (_0x1f1551) {
        return _0x1f1551();
      },
      aDRdg: "请使用\x20Chrome/Edge\x20最新版并确保\x20HTTPS\x20访问，或使用浏览器自带投屏按钮",
      IgnoX: "NEOar",
      BbAmy: "AEmbS",
      GoyNm: function (_0xb05fce, _0x17a0bc) {
        return _0xb05fce === _0x17a0bc;
      },
      AlEiJ: function (_0x1fb407, _0x1e0a77, _0x1411a8) {
        return _0x1fb407(_0x1e0a77, _0x1411a8);
      },
      jSddF: function (_0x40b894, _0x42c106, _0x33a56b) {
        return _0x40b894(_0x42c106, _0x33a56b);
      },
      EhcMC: function (_0x223a88, _0x482edd) {
        return _0x223a88 === _0x482edd;
      },
      VCfYJ: "Enter",
      rEGls: function (_0x3a3daf, _0x166b5c) {
        return _0x3a3daf === _0x166b5c;
      },
      leTtb: "Escape",
      tQeaW: "art_danmaku_area",
      UhVTF: "INPUT",
      wqLYy: "range",
      XNLqB: ".art-setting-item",
      pYBTO: ".art-setting-tooltip, .art-setting-value",
      GgrCV: "Opacity",
      OutJt: function (_0x25df0b, _0x5b569a) {
        return _0x25df0b === _0x5b569a;
      },
      DjhNz: "Size",
      cgLBM: function (_0x4a132e, _0x43ec02) {
        return _0x4a132e !== _0x43ec02;
      },
      THwnL: "VeQtQ",
      VrupD: "Bneom",
      pnktf: function (_0x48d84d, _0x100cd3) {
        return _0x48d84d + _0x100cd3;
      },
      svJQJ: function (_0x3528a0, _0x2c14d0) {
        return _0x3528a0 !== _0x2c14d0;
      },
      kXdQh: "透明度",
      EJdEn: function (_0x55def9, _0x38b4c4) {
        return _0x55def9 !== _0x38b4c4;
      },
      cDbrl: "mHtdr",
      OTzcI: "art_danmaku_opacity",
      IkeEr: "LISLq",
      FutBZ: "art_danmaku_fontsize",
      MqoEj: function (_0x59d9b7, _0xcaab9c) {
        return _0x59d9b7(_0xcaab9c);
      },
      fDDXp: function (_0x397170, _0xab79ae) {
        return _0x397170(_0xab79ae);
      },
      nWGBe: "true",
      DXBFB: function (_0xc26a92, _0x24cfdf) {
        return _0xc26a92(_0x24cfdf);
      },
      XoCpo: "#FFFFFF",
      YyxFL: function (_0x23449d, _0x1fedc7) {
        return _0x23449d + _0x1fedc7;
      },
      QYyMV: "m3u8",
      IuJMj: "auto",
      eQGTH: '<img src="img/state.svg">',
      fjnIo: "60秒",
      YffYo: "90秒",
      JcgIV: "跳过片尾",
      dWsRV: function (_0x641b84, _0x2737b2) {
        return _0x641b84 + _0x2737b2;
      },
      mAOFi: "自定义...",
      AYFdC: "%c 麒麟播放器 %c https://qilinblog.com ",
      tfyal: "color: #fff; background: #606060; padding:5px 0; border-radius: 5px 0 0 5px;",
      UkYgC: "art-layer-rotate",
      AKFov: "旋转屏幕",
      kGrts: "click",
      skrAC: "touchstart",
      vydds: "div",
      LBSbp: "art-layer-lock",
      LOPfZ: "锁定/解锁",
      xBRVq: "dblclick",
      WEYUP: "mousedown",
      ObEhV: "mouseup",
      FwTvh: "mousemove",
      WLpOx: "touchmove",
      CjhGO: "contextmenu",
      IIFDs: "art-layer-cast",
      NsfUy: "aria-label",
      uQFuv: "ready",
      VMRDJ: "contextmenu:show",
      QluRl: "playing",
      tvvOQ: "canplay",
      DgoFu: "pause",
      alcwp: "play",
      AJNlm: "video:ratechange",
      XYzgu: "volumechange",
      noaQP: "video:timeupdate",
      wCrEt: "artplayerPluginDanmuku:show",
      HzTay: "ymrOU",
      cuQwH: "input",
      TKJsv: "change",
    },
    _0x2a2ef1 = {
      skipIntro: _0x138822["MqoEj"](parseInt, localStorage["getItem"](_0x138822["oINee"]) || 0x0),
      skipOutro: parseInt(localStorage["getItem"](_0x138822["TkFaJ"]) || 0x0),
      danmakuArea: parseFloat(localStorage["getItem"]("art_danmaku_area") || 0.25),
      playbackRate: _0x138822["RxTqD"](parseFloat, localStorage["getItem"]("art_playback_rate") || 0x1),
      danmakuOpacity: parseFloat(localStorage["getItem"](_0x138822["OTzcI"]) || 0.5),
      danmakuFontSize: parseInt(localStorage["getItem"](_0x138822["FutBZ"]) || 0x16),
      danmakuVisible: _0x138822["Nysle"](localStorage["getItem"]("art_danmaku_visible"), _0x138822["TRYNe"]),
      volume: _0x138822["fDDXp"](parseFloat, localStorage["getItem"](_0x138822["OTlGQ"]) || 0.7),
      muted: localStorage["getItem"](_0x138822["IZsry"]) === _0x138822["nWGBe"],
    },
    _0x2195b4 = [],
    _0x514110 =
      (playerConfig["danmaku_enabled"] === undefined || playerConfig["danmaku_enabled"]) && playerConfig["danmaku_api"];
  _0x514110 &&
    _0x2195b4["push"](
      _0x138822["DXBFB"](artplayerPluginDanmuku, {
        danmuku: [],
        speed: 0xa,
        opacity: _0x2a2ef1["danmakuOpacity"],
        fontSize: _0x2a2ef1["danmakuFontSize"],
        color: _0x138822["XoCpo"],
        mode: 0x0,
        margin: [0xa, _0x138822["YyxFL"](_0x138822["vZudm"](0x1, _0x2a2ef1["danmakuArea"]) * 0x64, "%")],
        antiShield: !![],
        synchronousPlayback: ![],
        visible: _0x2a2ef1["danmakuVisible"],
      }),
    );
  ((art = new Artplayer({
    container: "#artplayer",
    url: _0x78f13e,
    id: playerConfig["videoUrl"],
    type: _0x138822["rEGls"](_0x5d87cf, "m3u8")
      ? _0x138822["QYyMV"]
      : _0x5d87cf === _0x138822["TbPld"]
        ? _0x138822["TbPld"]
        : _0x138822["IuJMj"],
    autoplay: !![],
    autoHide: !![],
    autoHideTime: 0x7d0,
    volume: _0x2a2ef1["volume"],
    muted: _0x2a2ef1["muted"],
    playbackRate: !![],
    icons: { state: _0x138822["eQGTH"] },
    setting: !![],
    pip: !![],
    fullscreen: !![],
    fullscreenWeb: ![],
    autoPlayback: !![],
    miniProgressBar: !![],
    flip: !![],
    rotate: !![],
    aspectRatio: !![],
    moreVideoAttr: { playsInline: !![], "webkit-playsinline": !![], "x5-playsinline": !![] },
    settings: [
      {
        html: "跳过片头",
        tooltip: _0x2a2ef1["skipIntro"] ? _0x138822["gwYDD"](_0x2a2ef1["skipIntro"], "秒") : "关闭",
        selector: [
          { html: "关闭", value: 0x0 },
          { html: _0x138822["fjnIo"], value: 0x3c },
          { html: _0x138822["YffYo"], value: 0x5a },
          { html: "自定义...", value: _0x138822["hAPSz"] },
        ],
        onSelect: function (_0x253a6d) {
          const _0x35634e = _0x564681,
            _0x5a79e4 = {
              cptdN: function (_0x49d8cf, _0x4c63c2) {
                return _0x138822["DTxmf"](_0x49d8cf, _0x4c63c2);
              },
              ESpdi: function (_0x10f4dd, _0x5801fd, _0x591c10) {
                const _0xf8ec5a = _0x12d4;
                return _0x138822["MyhUf"](_0x10f4dd, _0x5801fd, _0x591c10);
              },
            };
          if (_0x138822["FHaoh"](_0x253a6d["value"], _0x138822["hAPSz"])) {
            const _0x5f3e1f = _0x2a2ef1["skipIntro"] ? _0x2a2ef1["skipIntro"] + "秒" : "关闭";
            return (
              showInputModal("请输入跳过片头的秒数", _0x2a2ef1["skipIntro"] || 0x0, (_0x1529fa) => {
                const _0x198168 = _0x35634e;
                if (_0x138822["FHaoh"](_0x138822["qhTHm"], _0x138822["qhTHm"])) {
                  ((_0x2a2ef1["skipIntro"] = _0x1529fa), localStorage["setItem"]("art_skip_intro", _0x1529fa));
                  const _0x36a744 = _0x1529fa ? _0x138822["gwYDD"](_0x1529fa, "秒") : "关闭";
                  (_0x138822["MyhUf"](updateSettingTooltip, _0x138822["OKlVl"], _0x36a744),
                    (art["notice"]["show"] = "已设置跳过片头 " + _0x1529fa + "\x20秒"));
                } else {
                  ((_0x50022c["skipIntro"] = _0x2f97b3), _0x56a866["setItem"]("art_skip_intro", _0x267888));
                  const _0x14b9f6 = _0x185ee3 ? _0x5a79e4["cptdN"](_0x39c662, "秒") : "关闭";
                  (_0x5a79e4["ESpdi"](_0x4d7373, "跳过片头", _0x14b9f6),
                    (_0x146047["notice"]["show"] = "已设置跳过片头 " + _0x4ca5df + "\x20秒"));
                }
              }),
              _0x5f3e1f
            );
          }
          return (
            (_0x2a2ef1["skipIntro"] = _0x253a6d["value"]),
            localStorage["setItem"](_0x138822["oINee"], _0x253a6d["value"]),
            _0x253a6d["html"]
          );
        },
      },
      {
        html: _0x138822["JcgIV"],
        tooltip: _0x2a2ef1["skipOutro"] ? _0x138822["dWsRV"](_0x2a2ef1["skipOutro"], "秒") : "关闭",
        selector: [
          { html: "关闭", value: 0x0 },
          { html: "60秒", value: 0x3c },
          { html: _0x138822["YffYo"], value: 0x5a },
          { html: _0x138822["mAOFi"], value: "custom" },
        ],
        onSelect: function (_0x2bcb64) {
          const _0x49179c = _0x564681,
            _0x50626c = {
              xyjXT: _0x138822["KBGcU"],
              xVqFv: _0x138822["TkFaJ"],
              IVQZh: function (_0xdb5b, _0x1c2b92) {
                return _0xdb5b + _0x1c2b92;
              },
              elNyW: function (_0x22eee3, _0x2ae565, _0x2248e7) {
                return _0x22eee3(_0x2ae565, _0x2248e7);
              },
              RxcWS: "跳过片尾",
            };
          if (_0x138822["ytTEj"](_0x2bcb64["value"], _0x138822["hAPSz"])) {
            if (_0x138822["ytTEj"]("XYQsB", "kKWle")) {
              const _0x1eb0df = new _0x3509a2({ maxBufferLength: 0x12c, maxMaxBufferLength: 0x258 });
              (_0x1eb0df["loadSource"](_0x97166), _0x1eb0df["attachMedia"](_0x226543));
            } else {
              const _0x5041b8 = _0x2a2ef1["skipOutro"] ? _0x138822["TYrfr"](_0x2a2ef1["skipOutro"], "秒") : "关闭";
              return (
                _0x138822["mCydX"](showInputModal, _0x138822["AUtzb"], _0x2a2ef1["skipOutro"] || 0x0, (_0x443760) => {
                  const _0x57b8ab = _0x49179c;
                  if ("NYlAa" === _0x50626c["xyjXT"]) {
                    ((_0x2a2ef1["skipOutro"] = _0x443760), localStorage["setItem"](_0x50626c["xVqFv"], _0x443760));
                    const _0x1bc0e7 = _0x443760 ? _0x50626c["IVQZh"](_0x443760, "秒") : "关闭";
                    (_0x50626c["elNyW"](updateSettingTooltip, _0x50626c["RxcWS"], _0x1bc0e7),
                      (art["notice"]["show"] = "已设置跳过片尾 " + _0x443760 + "\x20秒"));
                  } else
                    _0x1e73c3 =
                      '<video src="' +
                      _0x1328ac["content"] +
                      '" autoplay muted loop style="max-width:100%; max-height:100%"></video>';
                }),
                _0x5041b8
              );
            }
          }
          return (
            (_0x2a2ef1["skipOutro"] = _0x2bcb64["value"]),
            localStorage["setItem"](_0x138822["TkFaJ"], _0x2bcb64["value"]),
            _0x2bcb64["html"]
          );
        },
      },
    ],
    customType: {
      m3u8: function (_0x25a044, _0x6b1c12) {
        const _0x4f57da = _0x564681;
        if (Hls["isSupported"]()) {
          if (_0x138822["ovFFV"]("UySxF", "UySxF"))
            _0x29fdab(() => {
              _0x1216b9();
            }, 0x1f40);
          else {
            const _0x32966d = new Hls({ maxBufferLength: 0x12c, maxMaxBufferLength: 0x258 });
            (_0x32966d["loadSource"](_0x6b1c12), _0x32966d["attachMedia"](_0x25a044));
          }
        } else _0x25a044["canPlayType"](_0x138822["eAqpD"]) && (_0x25a044["src"] = _0x6b1c12);
      },
      flv: function (_0x116f31, _0x2a5780) {
        const _0x167854 = _0x564681;
        if (flvjs["isSupported"]()) {
          const _0x3cba6e = flvjs["createPlayer"]({ type: _0x138822["TbPld"], url: _0x2a5780 });
          (_0x3cba6e["attachMediaElement"](_0x116f31), _0x3cba6e["load"]());
        }
      },
    },
    plugins: _0x2195b4,
  })),
    console["log"](
      _0x138822["AYFdC"],
      _0x138822["tfyal"],
      "background:\x20#409EFF;\x20padding:5px\x200;\x20border-radius:\x200\x205px\x205px\x200;\x20color:\x20#fff;",
    ),
    (function _0x158ebe() {
      const _0x49bfe9 = _0x564681,
        _0x4b3bbb = document["getElementById"](_0x138822["xDjzY"]);
      if (_0x4b3bbb) _0x4b3bbb["style"]["display"] = _0x138822["GzXxx"];
      document["body"]["classList"]["remove"](_0x138822["sHRBY"]);
    })());
  const _0x285dd1 = art["template"]["$player"],
    _0x9575f1 = document["createElement"]("div");
  ((_0x9575f1["className"] = _0x138822["UkYgC"]),
    (_0x9575f1["title"] = _0x138822["AKFov"]),
    (_0x9575f1["innerHTML"] =
      '\n        <svg width="24" height="24" viewBox="0 0 24 24" fill="#FFFFFF">\n            <path d="M10.25 1.75c-0.6-0.6-1.5-0.6-2.1 0s-0.6 1.5 0 2.1l1.95 1.95c-3.1 0.7-5.35 3.5-5.35 6.7 0 3.85 3.15 7 7 7s7-3.15 7-7c0-1.65-0.6-3.2-1.6-4.45l1.45-1.45c1.3 1.6 2.15 3.65 2.15 5.9 0 5.1-4.15 9.25-9.25 9.25s-9.25-4.15-9.25-9.25c0-4.15 2.75-7.7 6.6-8.8l-1.55-1.55c-0.6-0.6-0.6-1.5 0-2.1s1.5-0.6 2.1 0l4.25 4.25c0.6 0.6 0.6 1.5 0 2.1l-4.25 4.25c-0.3 0.3-0.7 0.45-1.05 0.45s-0.75-0.15-1.05-0.45z"></path>\n            <path d="M0 0h24v24H0z" fill="none"/>\n        </svg>\n    '),
    _0x9575f1["addEventListener"](_0x138822["kGrts"], (_0x48040a) => {
      const _0x59306a = _0x564681,
        _0x3b4a9c = { LCJiu: _0x138822["KVsuL"], UBVUB: _0x138822["pjUCd"] };
      (_0x48040a["stopPropagation"](), _0x48040a["preventDefault"]());
      const _0x4b7b6b = (_0x262316) => {
          const _0x312d46 = _0x59306a,
            _0x1586c4 = {
              CbHuJ: "pause",
              tjGmV: function (_0x4b96b1) {
                const _0xa7d012 = _0x12d4;
                return _0x138822["RJzLc"](_0x4b96b1);
              },
              uPvFJ: _0x138822["FBanr"],
              WSTcx: function (_0x395b6a, _0x539645, _0x103843) {
                return _0x138822["uadGf"](_0x395b6a, _0x539645, _0x103843);
              },
              RRNoJ: function (_0x3a0b5f, _0x417349) {
                const _0x1625a5 = _0x312d46;
                return _0x138822["WAbJJ"](_0x3a0b5f, _0x417349);
              },
              fXhOb: "XQmxn",
              KTMkl: "rbwLS",
              gtHwK: function (_0x4b701c, _0x33b64f) {
                return _0x4b701c !== _0x33b64f;
              },
              ImKIZ: "BMBMq",
              JxDSd: _0x138822["HPdcN"],
              QjWpk: function (_0x4b1b8b, _0x3e4679) {
                const _0x559806 = _0x312d46;
                return _0x138822["RxTqD"](_0x4b1b8b, _0x3e4679);
              },
              qlfZC: "API\x20unavailable",
            };
          if (_0x138822["cGdHE"](_0x138822["FneVe"], "hsItU"))
            return new Promise((_0x232afe, _0xe4477a) => {
              const _0x302c0a = _0x312d46,
                _0x243a2f = {
                  LdfWE: _0x1586c4["CbHuJ"],
                  YDIxI: function (_0x153d9b, _0x29341a) {
                    return _0x153d9b(_0x29341a);
                  },
                  lMtCK: function (_0x12c6b5, _0xb5022c) {
                    return _0x12c6b5 >= _0xb5022c;
                  },
                  QVQoR: function (_0x16063b) {
                    const _0x1c58c5 = _0x302c0a;
                    return _0x1586c4["tjGmV"](_0x16063b);
                  },
                  dUqdK: _0x1586c4["uPvFJ"],
                  OFXsX: function (_0x4c8ad9, _0x59f665, _0x41b7fe) {
                    const _0x478062 = _0x302c0a;
                    return _0x1586c4["WSTcx"](_0x4c8ad9, _0x59f665, _0x41b7fe);
                  },
                };
              if (_0x1586c4["RRNoJ"](_0x1586c4["fXhOb"], _0x1586c4["KTMkl"])) {
                const _0x1f0f9f = {
                  yJzqG: function (_0x3057a6) {
                    return _0x3057a6();
                  },
                };
                (_0x241ed9["on"](_0x243a2f["LdfWE"], () => {
                  _0x1f0f9f["yJzqG"](_0xe62b91);
                }),
                  _0x639620["on"]("play", () => {
                    _0x31667d();
                  }));
              } else {
                if (screen["orientation"] && screen["orientation"]["lock"])
                  screen["orientation"]["lock"](_0x262316)["then"](_0x232afe)["catch"](_0xe4477a);
                else {
                  if (_0x1586c4["gtHwK"](_0x1586c4["ImKIZ"], _0x1586c4["JxDSd"]))
                    _0x1586c4["QjWpk"](_0xe4477a, new Error(_0x1586c4["qlfZC"]));
                  else {
                    const _0x133d44 = _0x243a2f["YDIxI"](_0x5f0dca, _0x20e544["value"]);
                    !_0x3d04ea(_0x133d44) && _0x243a2f["lMtCK"](_0x133d44, 0x0)
                      ? (_0x243a2f["YDIxI"](_0x2e0e53, _0x133d44), _0x243a2f["QVQoR"](_0x59d0c5))
                      : ((_0x3e8aa0["style"]["borderColor"] = _0x243a2f["dUqdK"]),
                        (_0x3b212a["style"]["transform"] = "translateX(5px)"),
                        _0xedc2b(() => (_0x50111e["style"]["transform"] = "translateX(-5px)"), 0x32),
                        _0x243a2f["OFXsX"](_0x100322, () => (_0x13942f["style"]["transform"] = "none"), 0x64));
                  }
                }
              }
            });
          else {
            const _0x51a6b8 = _0x5430f2["createElement"](_0x3b4a9c["LCJiu"]);
            ((_0x51a6b8["textContent"] =
              "\n        .art-custom-modal {\n            position: fixed;\n            top: 0;\n            left: 0;\n            width: 100%;\n            height: 100%;\n            background: rgba(0, 0, 0, 0.7);\n            display: flex;\n            justify-content: center;\n            align-items: center;\n            z-index: 9999;\n            opacity: 0;\n            transition: opacity 0.2s;\n            font-family: sans-serif;\n        }\n        .art-custom-modal.show {\n            opacity: 1;\n        }\n        .art-custom-modal-content {\n            background: rgba(30, 30, 30, 0.95);\n            backdrop-filter: blur(10px);\n            padding: 24px;\n            border-radius: 12px;\n            width: 320px;\n            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);\n            text-align: center;\n            transform: scale(0.9);\n            transition: transform 0.2s;\n            border: 1px solid rgba(255, 255, 255, 0.1);\n        }\n        .art-custom-modal.show .art-custom-modal-content {\n            transform: scale(1);\n        }\n        .art-custom-modal h3 {\n            margin: 0 0 20px 0;\n            color: #fff;\n            font-size: 18px;\n            font-weight: 500;\n        }\n        .art-custom-modal input {\n            width: 100%;\n            padding: 12px;\n            background: #444;\n            border: 2px solid #555;\n            border-radius: 8px;\n            color: #fff;\n            font-size: 16px;\n            margin-bottom: 24px;\n            outline: none;\n            box-sizing: border-box;\n            transition: border-color 0.2s;\n        }\n        .art-custom-modal input:focus {\n            border-color: #00aaff;\n            background: #3a3a3a;\n        }\n        .art-custom-modal-btns {\n            display: flex;\n            justify-content: space-between;\n            gap: 12px;\n        }\n        .art-custom-modal-btn {\n            flex: 1;\n            padding: 10px 0;\n            border: none;\n            border-radius: 6px;\n            cursor: pointer;\n            font-size: 15px;\n            transition: all 0.2s;\n            font-weight: 500;\n        }\n        .art-custom-modal-btn.cancel {\n            background: #555;\n            color: #eee;\n        }\n        .art-custom-modal-btn.cancel:hover {\n            background: #666;\n        }\n        .art-custom-modal-btn.confirm {\n            background: #00aaff;\n            color: #fff;\n        }\n        .art-custom-modal-btn.confirm:hover {\n            background: #00aaff;\n        }\n    "),
              _0x3c6227["head"]["appendChild"](_0x51a6b8));
          }
        },
        _0x3f5821 = () => {
          const _0x348c32 = _0x59306a,
            _0x99f618 = {
              ojqTv: function (_0x3cbf49) {
                const _0x26710b = _0x12d4;
                return _0x138822["EkkiT"](_0x3cbf49);
              },
            };
          if (_0x138822["Nysle"](art["rotate"], 0x0)) {
            if (!document["fullscreenElement"]) art["rotate"] = 0x0;
            else {
              if (_0x138822["GetSP"](_0x138822["pVjNO"], _0x138822["pVjNO"]))
                return Promise["reject"](new Error("CSS mode"));
              else _0x34cee0["error"](_0x3b4a9c["UBVUB"], _0x33aa4f);
            }
          }
          if (!document["fullscreenElement"]) {
            if (_0x138822["cVCHm"]("xLYZM", _0x138822["AxiHf"]))
              return (
                (art["fullscreen"] = !![]),
                new Promise((_0x47d7d9) => setTimeout(_0x47d7d9, 0xc8))["then"](() => _0x4b7b6b("landscape"))
              );
            else
              _0x547e96 =
                '<video src="' +
                _0x184335["content"] +
                '" autoplay muted style="max-width:100%; max-height:100%"></video>';
          } else {
            if (_0x138822["aslkJ"](_0x138822["MfSBE"], _0x138822["MfSBE"])) _0x99f618["ojqTv"](_0x293087);
            else {
              if (
                screen["orientation"] &&
                screen["orientation"]["type"] &&
                screen["orientation"]["type"]["includes"](_0x138822["QZAOS"])
              )
                return _0x138822["RxTqD"](_0x4b7b6b, _0x138822["uGBet"]);
              return (
                (art["fullscreen"] = ![]),
                screen["orientation"] && screen["orientation"]["unlock"] && screen["orientation"]["unlock"](),
                Promise["resolve"]()
              );
            }
          }
        };
      _0x138822["RJzLc"](_0x3f5821)["catch"]((_0x4b0b13) => {
        const _0x26260c = _0x59306a;
        console["log"](_0x138822["wbuoi"], _0x4b0b13);
        if (art["rotate"] === 0x0) {
          ((art["rotate"] = 0x5a), (art["notice"]["show"] = "横屏"));
          if (!document["fullscreenElement"]) art["fullscreen"] = !![];
        } else {
          ((art["rotate"] = 0x0), (art["notice"]["show"] = _0x138822["SdzpF"]));
          if (document["fullscreenElement"]) art["fullscreen"] = ![];
        }
      });
    }),
    _0x9575f1["addEventListener"](
      _0x138822["skrAC"],
      (_0x1fac67) => {
        const _0x5dc6b9 = _0x564681,
          _0x43aa7b = { GDGyI: _0x138822["xDjzY"] };
        if (_0x138822["GetSP"]("yYLBC", "yYLBC")) _0x1fac67["stopPropagation"]();
        else {
          _0x3302c1["getElementById"](_0x43aa7b["GDGyI"])["style"]["display"] = "none";
          const _0xa820eb = _0x54d2bd["getElementById"]("artplayer");
          _0xa820eb["innerHTML"] =
            '\n        <div style="color: #fff; text-align: center; padding-top: 20%; font-family: sans-serif;">\n            <div style="font-size: 18px;">' +
            _0x1d623d +
            "</div>\n        </div>\n    ";
        }
      },
      { passive: ![] },
    ),
    _0x285dd1["appendChild"](_0x9575f1));
  const _0x4ae7b8 = document["createElement"](_0x138822["vydds"]);
  ((_0x4ae7b8["className"] = _0x138822["LBSbp"]),
    (_0x4ae7b8["title"] = _0x138822["LOPfZ"]),
    (_0x4ae7b8["innerHTML"] =
      '\n        <!-- 开锁图标 -->\n        <svg class="icon-unlock" width="24" height="24" viewBox="0 0 24 24" fill="#FFFFFF" style="display:block">\n            <path d="M12 17a2 2 0 1 0 0-4 2 2 0 0 0 0 4zm6-9h-1V6a5 5 0 0 0-10 0h2a3 3 0 1 1 6 0v2H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V10a2 2 0 0 0-2-2z"></path>\n        </svg>\n        <!-- 闭锁图标 -->\n        <svg class="icon-lock" width="24" height="24" viewBox="0 0 24 24" fill="#FFFFFF" style="display:none">\n            <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"></path>\n        </svg>\n    '),
    _0x4ae7b8["addEventListener"](_0x138822["kGrts"], (_0x45980a) => {
      const _0x50e40e = _0x564681;
      (_0x45980a["stopPropagation"](), _0x45980a["preventDefault"]());
      const _0x58d84a = _0x285dd1["classList"]["contains"]("art-locked-mode"),
        _0x4c57b9 = _0x4ae7b8["querySelector"](_0x138822["tcpuH"]),
        _0x9296b1 = _0x4ae7b8["querySelector"](_0x138822["KBljJ"]);
      if (_0x58d84a)
        _0x138822["ovOuW"](_0x138822["YxTKe"], _0x138822["YxTKe"])
          ? (_0x71e19["classList"]["remove"](_0x138822["hKdrt"]),
            _0x138822["BRxVE"](_0x3e2ab2, () => _0xb0f486["remove"](), 0xc8))
          : (_0x285dd1["classList"]["remove"]("art-locked-mode"),
            (_0x4c57b9["style"]["display"] = _0x138822["NXFko"]),
            (_0x9296b1["style"]["display"] = _0x138822["GzXxx"]),
            (art["notice"]["show"] = _0x138822["qcrlW"]));
      else {
        if (_0x138822["ofJeu"] === _0x138822["GgUHf"]) {
          if (!_0x4c0785["fullscreenElement"]) _0x2e1691["rotate"] = 0x0;
          else return _0x4fefb5["reject"](new _0x100622("CSS\x20mode"));
        } else
          (_0x285dd1["classList"]["add"]("art-locked-mode"),
            (_0x4c57b9["style"]["display"] = "none"),
            (_0x9296b1["style"]["display"] = "block"),
            (art["notice"]["show"] = _0x138822["IfnVZ"]));
      }
    }),
    _0x4ae7b8["addEventListener"](
      _0x138822["skrAC"],
      (_0x2f1077) => {
        const _0x6dbe57 = _0x564681,
          _0x43d5eb = {
            oLvmk: function (_0xdb86ba, _0x51cf5e) {
              const _0x248640 = _0x12d4;
              return _0x138822["fbNgq"](_0xdb86ba, _0x51cf5e);
            },
            ySPKX: function (_0x4458f7, _0x59b550) {
              const _0x2e5702 = _0x12d4;
              return _0x138822["iquLc"](_0x4458f7, _0x59b550);
            },
            XxXTR: function (_0x4ebbed, _0x29a89d) {
              return _0x138822["vZudm"](_0x4ebbed, _0x29a89d);
            },
            lJzsB: "弹幕已采样至",
          };
        if (_0x138822["GaiAs"] === _0x138822["pYrXj"]) {
          _0x42de94["sort"]((_0x21ec18, _0x4a85ac) => _0x21ec18["time"] - _0x4a85ac["time"]);
          const _0x5896fd = _0x43d5eb["oLvmk"](_0x1b058f["length"], _0x58253c),
            _0x38ac11 = [];
          for (let _0xa29062 = 0x0; _0x43d5eb["ySPKX"](_0xa29062, _0x5d301e); _0xa29062++) {
            _0x38ac11["push"](
              _0x3f8dbf[
                _0x590820["min"](
                  _0x51f8f3["floor"](_0xa29062 * _0x5896fd),
                  _0x43d5eb["XxXTR"](_0x333bdc["length"], 0x1),
                )
              ],
            );
          }
          ((_0x39289d = _0x38ac11),
            _0x4ecff5["log"](_0x43d5eb["lJzsB"], _0x4d1a9e, "条（原始", _0x5e1419["data"]["length"], "条）"));
        } else _0x2f1077["stopPropagation"]();
      },
      { passive: ![] },
    ),
    _0x285dd1["appendChild"](_0x4ae7b8));
  const _0x561545 = document["createElement"]("div");
  ((_0x561545["className"] = "art-lock-mask"),
    [
      "click",
      _0x138822["xBRVq"],
      _0x138822["WEYUP"],
      _0x138822["ObEhV"],
      _0x138822["FwTvh"],
      _0x138822["skrAC"],
      _0x138822["WLpOx"],
      "touchend",
      _0x138822["CjhGO"],
    ]["forEach"]((_0x362ff8) => {
      _0x561545["addEventListener"](
        _0x362ff8,
        (_0x36a927) => {
          const _0x570b85 = _0x12d4;
          (_0x36a927["stopPropagation"](), _0x36a927["preventDefault"]());
        },
        { passive: ![] },
      );
    }),
    _0x285dd1["appendChild"](_0x561545));
  const _0x4555bf = document["createElement"](_0x138822["vydds"]);
  ((_0x4555bf["className"] = _0x138822["IIFDs"]),
    (_0x4555bf["title"] = "投屏"),
    _0x4555bf["setAttribute"](_0x138822["NsfUy"], "投屏"),
    (_0x4555bf["innerHTML"] =
      '\n        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">\n            <path d="M2 16.1A5 5 0 0 1 5.9 20M2 12.05A9 9 0 0 1 9.95 20M2 8V6a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-6"/>\n            <line x1="2" y1="20" x2="2.01" y2="20"/>\n        </svg>\n    '),
    _0x4555bf["addEventListener"](_0x138822["kGrts"], (_0x55cbed) => {
      const _0x4ad146 = _0x564681,
        _0x557281 = {
          KENzP: _0x138822["GzXxx"],
          ygtGf: _0x138822["RMkAd"],
          bfRZt: _0x138822["RKgza"],
          OYDbr: function (_0x1ae88f, _0xd02542) {
            return _0x1ae88f(_0xd02542);
          },
          OLTOC: _0x138822["uLzXt"],
        };
      (_0x55cbed["stopPropagation"](), _0x55cbed["preventDefault"]());
      const _0x3d2f9d = art["video"];
      if (!_0x3d2f9d) {
        art["notice"]["show"] = _0x138822["LczOr"];
        return;
      }
      if (_0x138822["ovFFV"](_0x3d2f9d["disableRemotePlayback"], ![])) _0x3d2f9d["disableRemotePlayback"] = ![];
      if (_0x3d2f9d["remote"] && typeof _0x3d2f9d["remote"]["prompt"] === _0x138822["TrCFQ"]) {
        if (_0x138822["AqvNc"] !== _0x138822["AqvNc"])
          ((_0x5561ee["seek"] = _0x35d69b),
            (_0x50b819["notice"]["show"] = "已跳过片尾\x20" + _0x3e2d56["skipOutro"] + "\x20秒"));
        else {
          _0x3d2f9d["remote"]
            ["prompt"]()
            ["then"](() => {
              const _0x2c23d8 = _0x4ad146;
              art["notice"]["show"] = "已连接投屏设备";
            })
            ["catch"](() => {
              const _0x1b74b1 = _0x4ad146,
                _0xbdbce4 = {
                  YjWCL: _0x138822["cxhhl"],
                  VQOzW: _0x138822["ijwJq"],
                  nDFzH: "none",
                  flzPD: ".art-contextmenu-item",
                };
              if (_0x138822["ovOuW"](_0x138822["XFVea"], _0x138822["yQfZx"]))
                art["notice"]["show"] = _0x138822["fTeyL"];
              else {
                const _0x44ce18 = {
                  UVAjE: _0xbdbce4["YjWCL"],
                  vZuHa: _0xbdbce4["VQOzW"],
                  XHRsG: _0xbdbce4["nDFzH"],
                  FPNeT: _0xbdbce4["flzPD"],
                };
                _0x2a8297(() => {
                  const _0x308c1c = _0x1b74b1;
                  _0x455af9["querySelectorAll"](_0x44ce18["FPNeT"])["forEach"]((_0x334575) => {
                    const _0x482934 = _0x308c1c;
                    (_0x334575["textContent"]["trim"]()["includes"](_0x44ce18["UVAjE"]) ||
                      _0x334575["querySelector"](_0x44ce18["vZuHa"])) &&
                      (_0x334575["style"]["display"] = _0x44ce18["XHRsG"]);
                  });
                  const _0x4050b4 = _0x533090["querySelector"](".art-contextmenu-version");
                  if (_0x4050b4) _0x4050b4["style"]["display"] = _0x44ce18["XHRsG"];
                }, 0xa);
              }
            });
          return;
        }
      }
      if (
        window["__castApiAvailable"] &&
        window["cast"] &&
        window["cast"]["framework"] &&
        window["chrome"] &&
        window["chrome"]["cast"]
      ) {
        if (_0x138822["pPnOB"] === _0x138822["pjlkz"]) _0x261cb4["style"]["display"] = _0x557281["KENzP"];
        else {
          try {
            if (_0x138822["avdCj"]("qfgDs", _0x138822["NuuDk"])) {
              var _0x23cdbc = window["cast"]["framework"]["CastContext"]["getInstance"](),
                _0x4d6370 = _0x23cdbc["getCurrentSession"](),
                _0x30a350 = (art["option"] && art["option"]["url"]) || art["url"] || "";
              if (!_0x30a350) {
                if (_0x138822["EnjpE"] === _0x138822["EnjpE"]) {
                  art["notice"]["show"] = "无法获取视频地址";
                  return;
                } else
                  _0x179f6a["addEventListener"](
                    _0x20ddd9,
                    (_0xab828a) => {
                      const _0x18e495 = _0x4ad146;
                      (_0xab828a["stopPropagation"](), _0xab828a["preventDefault"]());
                    },
                    { passive: ![] },
                  );
              }
              var _0x102027 = "video/mp4";
              if (/\.m3u8(\?|$)/i["test"](_0x30a350)) _0x102027 = _0x138822["RElzr"];
              else {
                if (/\.flv(\?|$)/i["test"](_0x30a350)) _0x102027 = "video/x-flv";
              }
              function _0x473e90(_0x5916c3) {
                const _0x19984a = _0x4ad146,
                  _0x288f32 = { uzCXt: _0x138822["VnCre"] };
                var _0x465f02 = new window["chrome"]["cast"]["media"]["MediaInfo"](_0x30a350, _0x102027),
                  _0x63aec1 = new window["chrome"]["cast"]["media"]["LoadRequest"](_0x465f02);
                ((_0x63aec1["currentTime"] = art["currentTime"] || 0x0),
                  _0x5916c3["loadMedia"](_0x63aec1)
                    ["then"](function () {
                      const _0x61d2bf = _0x19984a;
                      art["notice"]["show"] = _0x288f32["uzCXt"];
                    })
                    ["catch"](function () {
                      const _0x268223 = _0x19984a;
                      art["notice"]["show"] = _0x557281["ygtGf"];
                    }));
              }
              _0x4d6370
                ? _0x138822["GGHGv"](_0x473e90, _0x4d6370)
                : _0x138822["Fzyke"] === _0x138822["Fzyke"]
                  ? _0x23cdbc["requestSession"]()
                      ["then"](function (_0x32835a) {
                        const _0xf83b82 = _0x4ad146;
                        _0x138822["RxTqD"](_0x473e90, _0x32835a);
                      })
                      ["catch"](function () {
                        const _0x2de5fe = _0x4ad146;
                        _0x138822["ZxLZK"] === _0x138822["QQJCF"]
                          ? _0x4f5230["orientation"]["unlock"]()
                          : (art["notice"]["show"] = _0x138822["wrqbT"]);
                      })
                  : (_0x5c1cc9["notice"]["show"] = _0x557281["bfRZt"]);
            } else _0x557281["OYDbr"](_0x3e7a0b, _0x557281["OLTOC"]);
          } catch (_0x2b8027) {
            art["notice"]["show"] = "投屏初始化失败";
          }
          return;
        }
      }
      var _0x25afdc = (navigator["userAgent"] || "")["toLowerCase"]();
      _0x25afdc["indexOf"](_0x138822["xQGpe"]) !== -0x1 || _0x25afdc["indexOf"](_0x138822["dUuul"]) !== -0x1
        ? (art["notice"]["show"] = _0x138822["mhBFU"])
        : (art["notice"]["show"] = "请使用 Chrome/Edge 最新版并确保 HTTPS 访问，或使用浏览器自带投屏按钮");
    }),
    _0x4555bf["addEventListener"]("touchstart", (_0xa9237b) => _0xa9237b["stopPropagation"](), { passive: ![] }),
    _0x285dd1["appendChild"](_0x4555bf),
    art["once"](_0x138822["uQFuv"], () => {
      const _0x44405d = _0x564681,
        _0x7f04bb = {
          GBKpr: function (_0x3be566, _0x185377) {
            return _0x3be566 > _0x185377;
          },
          JyMxU: function (_0x22e530, _0x39eacd) {
            const _0x292d41 = _0x12d4;
            return _0x138822["iquLc"](_0x22e530, _0x39eacd);
          },
          cZPhL: function (_0x57c8f8, _0x4f0b08) {
            return _0x138822["vZudm"](_0x57c8f8, _0x4f0b08);
          },
        };
      if (_0x138822["ovFFV"]("agcnr", _0x138822["uhTam"]))
        _0x138822["uadGf"](
          setTimeout,
          () => {
            _0x138822["EkkiT"](loadDanmuku);
          },
          0x1f40,
        );
      else {
        const _0x9f24df = _0x3895ea["currentTime"],
          _0x1e9a1c = _0x32b02c["duration"];
        (_0x7f04bb["GBKpr"](_0x1b035a["skipIntro"], 0x0) &&
          _0x7f04bb["JyMxU"](_0x9f24df, _0x57d477["skipIntro"]) &&
          ((_0x426697["seek"] = _0x3dd56a["skipIntro"]),
          (_0xf7bf8b["notice"]["show"] = "已跳过片头 " + _0x4331cc["skipIntro"] + "\x20秒")),
          _0x7f04bb["GBKpr"](_0x1e4674["skipOutro"], 0x0) &&
            _0x1e9a1c > 0x0 &&
            _0x7f04bb["cZPhL"](_0x1e9a1c, _0x9f24df) < _0x35a0cd["skipOutro"] &&
            _0x7f04bb["GBKpr"](_0x7f04bb["cZPhL"](_0x1e9a1c, _0x9f24df), 0x1) &&
            ((_0x14d688["seek"] = _0x1e9a1c),
            (_0x4191d3["notice"]["show"] = "已跳过片尾\x20" + _0x1c53b4["skipOutro"] + "\x20秒")));
      }
    }),
    art["on"](_0x138822["VMRDJ"], () => {
      const _0xd4ff68 = _0x564681,
        _0x2b8a66 = { Uvcak: _0x138822["cxhhl"], QheSh: _0x138822["ijwJq"], sYmJu: "none" };
      _0x138822["uXVkZ"](
        setTimeout,
        () => {
          const _0x33fe15 = _0xd4ff68;
          document["querySelectorAll"](_0x138822["UUUXv"])["forEach"]((_0x33797c) => {
            const _0x9ebb90 = _0x33fe15;
            (_0x33797c["textContent"]["trim"]()["includes"](_0x2b8a66["Uvcak"]) ||
              _0x33797c["querySelector"](_0x2b8a66["QheSh"])) &&
              (_0x33797c["style"]["display"] = _0x2b8a66["sYmJu"]);
          });
          const _0x22b178 = document["querySelector"](_0x138822["zhFdo"]);
          if (_0x22b178) _0x22b178["style"]["display"] = _0x138822["GzXxx"];
        },
        0xa,
      );
    }),
    art["on"](_0x138822["uQFuv"], () => {
      const _0x46ffbf = _0x564681,
        _0x36791f = { IKltJ: _0x138822["sbbBE"], VlIia: "block" };
      if ("eMuhB" !== "eMuhB")
        (_0xb8337["classList"]["remove"](_0x36791f["IKltJ"]),
          (_0x20d34e["style"]["display"] = _0x36791f["VlIia"]),
          (_0x4619c6["style"]["display"] = "none"),
          (_0x1a4733["notice"]["show"] = "已解锁"));
      else {
        const _0x411797 = document["getElementById"]("loading-box");
        if (_0x411797) _0x411797["style"]["display"] = _0x138822["GzXxx"];
        document["body"]["classList"]["remove"](_0x138822["sHRBY"]);
      }
    }),
    art["on"](_0x138822["QluRl"], () => {
      const _0x18f50d = _0x564681,
        _0x69873b = document["getElementById"](_0x138822["xDjzY"]);
      if (_0x69873b) _0x69873b["style"]["display"] = "none";
      document["body"]["classList"]["remove"](_0x138822["sHRBY"]);
    }),
    art["on"](_0x138822["tvvOQ"], () => {
      const _0x3f1b69 = _0x564681,
        _0x13e194 = document["getElementById"](_0x138822["xDjzY"]);
      if (_0x13e194) _0x13e194["style"]["display"] = _0x138822["GzXxx"];
      document["body"]["classList"]["remove"]("loading");
    }),
    art["on"]("error", () => {
      const _0x552d33 = _0x564681,
        _0x2df12f = document["getElementById"](_0x138822["xDjzY"]);
      if (_0x2df12f) _0x2df12f["style"]["display"] = "none";
      document["body"]["classList"]["remove"]("loading");
    }));
  playerConfig["ads"]["pause"]["enabled"] &&
    (art["on"](_0x138822["DgoFu"], () => {
      showPauseAd();
    }),
    art["on"](_0x138822["alcwp"], () => {
      closePauseAd();
    }));
  (art["on"](_0x138822["AJNlm"], () => {
    const _0x46e74c = _0x564681,
      _0x54b4f6 = art["playbackRate"];
    localStorage["setItem"](_0x138822["tRdxx"], _0x54b4f6);
  }),
    art["on"](_0x138822["XYzgu"], () => {
      const _0x6b0e75 = _0x564681;
      (localStorage["setItem"](_0x138822["OTlGQ"], art["volume"]),
        localStorage["setItem"](_0x138822["IZsry"], art["muted"]));
    }),
    art["on"](_0x138822["noaQP"], () => {
      const _0x419a8a = _0x564681,
        _0x217b6e = { zLXsY: _0x138822["xSAuU"] },
        _0x3e1543 = art["currentTime"],
        _0x368f1a = art["duration"];
      (_0x138822["jmRaT"](_0x2a2ef1["skipIntro"], 0x0) &&
        _0x138822["HNSay"](_0x3e1543, _0x2a2ef1["skipIntro"]) &&
        ((art["seek"] = _0x2a2ef1["skipIntro"]),
        (art["notice"]["show"] = "已跳过片头\x20" + _0x2a2ef1["skipIntro"] + "\x20秒")),
        _0x138822["jmRaT"](_0x2a2ef1["skipOutro"], 0x0) &&
          _0x368f1a > 0x0 &&
          _0x368f1a - _0x3e1543 < _0x2a2ef1["skipOutro"] &&
          _0x138822["xbSjt"](_0x138822["vZudm"](_0x368f1a, _0x3e1543), 0x1) &&
          (_0x138822["avdCj"](_0x138822["UrQZJ"], "TofQi")
            ? _0x4d40cc["playbackRate"] !== _0x1da4f1["playbackRate"] &&
              ((_0x4845c6["playbackRate"] = _0x17dd49["playbackRate"]),
              _0x2ab034["log"](_0x217b6e["zLXsY"], _0x180ad1["playbackRate"]))
            : ((art["seek"] = _0x368f1a),
              (art["notice"]["show"] = "已跳过片尾 " + _0x2a2ef1["skipOutro"] + "\x20秒"))));
    }),
    art["on"](_0x138822["wCrEt"], () => {
      const _0x21b5db = _0x564681;
      (console["log"](_0x138822["JcUmb"]), localStorage["setItem"]("art_danmaku_visible", "true"));
    }),
    art["on"]("artplayerPluginDanmuku:hide", () => {
      const _0x37de36 = _0x564681;
      (console["log"](_0x138822["jmtuC"]), localStorage["setItem"]("art_danmaku_visible", _0x138822["TRYNe"]));
    }));
  if (_0x138822["svJQJ"](_0x2a2ef1["playbackRate"], 0x1)) {
    if (_0x138822["ovOuW"](_0x138822["HzTay"], "dQDhm")) {
      const _0x530bc5 = () => {
        const _0x28538a = _0x564681,
          _0x605a44 = { uWwwz: _0x138822["aDRdg"] };
        "YVTqG" === _0x138822["IgnoX"]
          ? _0x138822["kiIGJ"](_0x100007)
          : _0x138822["aslkJ"](art["playbackRate"], _0x2a2ef1["playbackRate"]) &&
            (_0x138822["ytTEj"]("AEmbS", _0x138822["BbAmy"])
              ? ((art["playbackRate"] = _0x2a2ef1["playbackRate"]),
                console["log"]("Restored playback rate:", _0x2a2ef1["playbackRate"]))
              : (_0x38ecb6["notice"]["show"] = _0x605a44["uWwwz"]));
      };
      (art["on"](_0x138822["uQFuv"], () => {
        const _0x3ee411 = _0x564681;
        _0x138822["GoyNm"]("AfrDI", "AfrDI")
          ? _0x138822["AlEiJ"](setTimeout, _0x530bc5, 0x1f4)
          : (_0x3acae0["innerText"] = _0x8e3aba + "秒后跳过");
      }),
        art["on"](_0x138822["alcwp"], () => {
          const _0x6afa1 = _0x564681;
          _0x138822["jSddF"](setTimeout, _0x530bc5, 0x1f4);
        }));
    } else {
      if (_0x138822["EhcMC"](_0x2d39ed["key"], _0x138822["VCfYJ"])) _0x7d3dff();
      if (_0x138822["rEGls"](_0x3bc4d6["key"], _0x138822["leTtb"])) _0x5e0262();
    }
  }
  const _0x374e67 = art["template"]["$setting"];
  _0x374e67 &&
    (_0x374e67["addEventListener"](_0x138822["cuQwH"], (_0x1954a6) => {
      const _0x5ea130 = _0x564681,
        _0x496daf = _0x1954a6["target"];
      if (
        _0x138822["cVCHm"](_0x496daf["tagName"], _0x138822["UhVTF"]) ||
        _0x138822["ovOuW"](_0x496daf["type"], _0x138822["wqLYy"])
      )
        return;
      const _0x1b34c8 = _0x496daf["closest"](_0x138822["XNLqB"]);
      if (!_0x1b34c8) return;
      const _0x513050 = _0x1b34c8["querySelector"](_0x138822["pYBTO"]);
      if (!_0x513050) return;
      const _0x276fac = _0x1b34c8["textContent"];
      let _0x2c3511 = _0x496daf["value"];
      if (
        _0x276fac["includes"]("透明度") ||
        _0x276fac["includes"](_0x138822["GgrCV"]) ||
        _0x276fac["includes"]("范围") ||
        _0x276fac["includes"]("Area")
      )
        _0x138822["OutJt"]("TCIoX", "mXqgx")
          ? _0xe805d6["template"]["$player"]["appendChild"](_0x2a91b4)
          : (_0x2c3511 = Math["round"](_0x2c3511 * 0x64) + "%");
      else {
        if (_0x276fac["includes"]("字号") || _0x276fac["includes"](_0x138822["DjhNz"]))
          _0x138822["cgLBM"](_0x138822["THwnL"], _0x138822["VrupD"])
            ? (_0x2c3511 = _0x138822["pnktf"](_0x2c3511, "px"))
            : _0x37d195["setItem"](_0x138822["tQeaW"], _0x441659);
        else (_0x276fac["includes"]("速度") || _0x276fac["includes"]("Speed")) && (_0x2c3511 = _0x2c3511 + "s");
      }
      _0x513050["innerText"] = _0x2c3511;
    }),
    _0x374e67["addEventListener"](_0x138822["TKJsv"], (_0x15e03f) => {
      const _0x2eca21 = _0x564681,
        _0x100f32 = {
          Wwftt: _0x138822["TkFaJ"],
          SAxfD: function (_0x46c2f8, _0x772415) {
            return _0x46c2f8 + _0x772415;
          },
          wFiiu: function (_0xb8ec9b, _0x2df313, _0x537545) {
            const _0x3418d6 = _0x2eca21;
            return _0x138822["uadGf"](_0xb8ec9b, _0x2df313, _0x537545);
          },
          jVrTv: "请输入跳过片尾的秒数",
        },
        _0x217f8a = _0x15e03f["target"];
      if (
        _0x138822["svJQJ"](_0x217f8a["tagName"], _0x138822["UhVTF"]) ||
        _0x138822["cVCHm"](_0x217f8a["type"], "range")
      )
        return;
      const _0x33a051 = _0x217f8a["closest"](_0x138822["XNLqB"]);
      if (!_0x33a051) return;
      const _0x55ed37 = _0x33a051["textContent"],
        _0x3ddaa3 = _0x138822["GGHGv"](parseFloat, _0x217f8a["value"]);
      if (_0x55ed37["includes"](_0x138822["kXdQh"]) || _0x55ed37["includes"](_0x138822["GgrCV"])) {
        if (_0x138822["EJdEn"](_0x138822["cDbrl"], _0x138822["cDbrl"])) {
          const _0x28a375 = _0x217f2f["skipOutro"] ? _0x100f32["SAxfD"](_0x587700["skipOutro"], "秒") : "关闭";
          return (
            _0xd3b2d2(_0x100f32["jVrTv"], _0x11ac2e["skipOutro"] || 0x0, (_0x3e039c) => {
              const _0x2e464c = _0x2eca21;
              ((_0x2dc06e["skipOutro"] = _0x3e039c), _0x786283["setItem"](_0x100f32["Wwftt"], _0x3e039c));
              const _0x337e9c = _0x3e039c ? _0x100f32["SAxfD"](_0x3e039c, "秒") : "关闭";
              (_0x100f32["wFiiu"](_0x9c2510, "跳过片尾", _0x337e9c),
                (_0x4989e3["notice"]["show"] = "已设置跳过片尾 " + _0x3e039c + "\x20秒"));
            }),
            _0x28a375
          );
        } else localStorage["setItem"](_0x138822["OTzcI"], _0x3ddaa3);
      } else {
        if (_0x55ed37["includes"]("字号") || _0x55ed37["includes"](_0x138822["DjhNz"]))
          _0x138822["IkeEr"] === _0x138822["IkeEr"]
            ? localStorage["setItem"](_0x138822["FutBZ"], _0x217f8a["value"])
            : (_0xa1339d["stopPropagation"](), _0x136d25["preventDefault"]());
        else
          (_0x55ed37["includes"]("范围") || _0x55ed37["includes"]("Area") || _0x55ed37["includes"]("显示区域")) &&
            localStorage["setItem"](_0x138822["tQeaW"], _0x3ddaa3);
      }
    }));
}
function showPauseAd() {
  const _0x3c68c1 = _0x2b2717,
    _0x51cd38 = {
      FieRp: "未选择设备或已取消",
      WLkPp: function (_0x4f5448, _0x2fe4f0) {
        return _0x4f5448(_0x2fe4f0);
      },
      ScvYT: function (_0x39ddc6) {
        return _0x39ddc6();
      },
      DiBfI: "_blank",
      WRNlW: "ad-pause",
      zXKCK: "ad-pause-container",
      mPeWj: function (_0x54e2a2, _0xa43b62) {
        return _0x54e2a2 === _0xa43b62;
      },
      tXRAQ: "deFLP",
      YwmeS: "ucQKb",
      NOOja: function (_0x49c765, _0x416483) {
        return _0x49c765 === _0x416483;
      },
      jNqYs: "SqoLT",
      TrTaw: "YHBcX",
    },
    _0x2f7204 = playerConfig["ads"]["pause"];
  if (!_0x2f7204 || !_0x2f7204["content"]) return;
  const _0xd79dac = document["getElementById"](_0x51cd38["WRNlW"]),
    _0x2f1122 = document["getElementById"](_0x51cd38["zXKCK"]);
  _0xd79dac["style"]["display"] = "flex";
  let _0x3188d3 = "";
  if (_0x51cd38["mPeWj"](_0x2f7204["type"], "video")) {
    if (_0x51cd38["tXRAQ"] === _0x51cd38["YwmeS"]) {
      const _0x45adc3 = {
        JuJvb: function (_0x5e4b4e, _0x46306c) {
          return _0x5e4b4e(_0x46306c);
        },
        OJgfB: _0x51cd38["FieRp"],
      };
      _0x190ca5["requestSession"]()
        ["then"](function (_0x392613) {
          const _0x429520 = _0x3c68c1;
          _0x45adc3["JuJvb"](_0x59a4f6, _0x392613);
        })
        ["catch"](function () {
          const _0x13cce9 = _0x3c68c1;
          _0x2057c3["notice"]["show"] = _0x45adc3["OJgfB"];
        });
    } else
      _0x3188d3 =
        "<video\x20src=\x22" +
        _0x2f7204["content"] +
        "\x22\x20autoplay\x20muted\x20loop\x20style=\x22max-width:100%;\x20max-height:100%\x22></video>";
  } else
    _0x51cd38["NOOja"](_0x51cd38["jNqYs"], _0x51cd38["TrTaw"])
      ? (_0x51cd38["WLkPp"](_0x57aac9, _0x122c25), _0x51cd38["ScvYT"](_0x37a8cb))
      : (_0x3188d3 = "<img\x20src=\x22" + _0x2f7204["content"] + '" style="max-width:100%; max-height:100%">');
  ((_0x2f1122["innerHTML"] = _0x3188d3),
    (_0x2f1122["onclick"] = (_0x956d46) => {
      const _0x1b6e5f = _0x3c68c1;
      _0x956d46["stopPropagation"]();
      if (_0x2f7204["link"]) window["open"](_0x2f7204["link"], _0x51cd38["DiBfI"]);
    }));
}
function closePauseAd() {
  const _0x40f168 = _0x2b2717;
  document["getElementById"]("ad-pause")["style"]["display"] = "none";
}
const MAX_DANMAKU = 0x1f40;
async function loadDanmuku() {
  const _0x122903 = _0x2b2717,
    _0x325279 = {
      MuSUQ: ".m3u8",
      aqaBF: "m3u8",
      mUDFj: ".flv",
      GvxWL: "flv",
      GeBGM: ".mp4",
      thHrp: "mp4",
      ewEwP: function (_0x5d3c4c, _0x3df2d0) {
        return _0x5d3c4c !== _0x3df2d0;
      },
      HtfGm: function (_0x363166, _0x553363) {
        return _0x363166 !== _0x553363;
      },
      xtWvh: function (_0x7746d4, _0x295f50) {
        return _0x7746d4 !== _0x295f50;
      },
      nZcbe: function (_0xb9a3a2, _0x46ef7a) {
        return _0xb9a3a2 !== _0x46ef7a;
      },
      AgLCz: function (_0x468957, _0x12be50) {
        return _0x468957(_0x12be50);
      },
      SnAaX: function (_0x277657, _0x1bc5d4) {
        return _0x277657 === _0x1bc5d4;
      },
      ycALt: "bottom",
      TpyZI: "#ffffff",
      AsUer: function (_0x587e21, _0x14cb0a) {
        return _0x587e21 || _0x14cb0a;
      },
      nrYln: function (_0x14357d, _0x13a113, _0x31fe33) {
        return _0x14357d(_0x13a113, _0x31fe33);
      },
      mRUQP: "跳过片尾",
      Qgpbk: function (_0x1b7d37, _0x34ef58) {
        return _0x1b7d37 === _0x34ef58;
      },
      TeSZb: function (_0x4e4df8, _0x5177a9) {
        return _0x4e4df8 + _0x5177a9;
      },
      cLJRM: function (_0x3773a6, _0xe70695, _0x45112f, _0x2ba062) {
        return _0x3773a6(_0xe70695, _0x45112f, _0x2ba062);
      },
      RYErT: "请输入跳过片尾的秒数",
      LVJHy: "art_skip_outro",
      pipBJ: "API\x20unavailable",
      Cqnav: function (_0x9cc9b9, _0x1236d8) {
        return _0x9cc9b9 !== _0x1236d8;
      },
      laEsU: "api/v3/?id=",
      WpMnM: function (_0x51d89b, _0x2fc5cf) {
        return _0x51d89b(_0x2fc5cf);
      },
      qQkrU: "jQPYb",
      xGyJp: "kANBy",
      FrDvz: function (_0x4196f7, _0x374b45) {
        return _0x4196f7 < _0x374b45;
      },
      zlYpu: "CIfVT",
      nQVmL: function (_0x3059fc, _0x5a2fd7) {
        return _0x3059fc !== _0x5a2fd7;
      },
      IkWYf: function (_0x35aefd, _0x5213bf) {
        return _0x35aefd > _0x5213bf;
      },
      GwdLj: function (_0x2940f8, _0x33d271) {
        return _0x2940f8 / _0x33d271;
      },
      mNuEe: function (_0x43fa02, _0x37ffcd) {
        return _0x43fa02 - _0x37ffcd;
      },
      aiPil: "弹幕已采样至",
      JADKy: "条（原始",
      gzyot: "wgwrL",
      UfIMw: function (_0x3c8023, _0xcb845d) {
        return _0x3c8023 === _0xcb845d;
      },
      NvBom: "DyyBj",
      XbdJC: "弹幕插件加载出错:",
      UzFsl: "当前插件列表:",
      pHFvp: "弹幕数据格式不正确:",
      qoWUI: "弹幕加载失败",
    };
  if (!playerConfig["danmaku_api"]) return;
  if (_0x325279["Cqnav"](playerConfig["danmaku_enabled"], undefined) && !playerConfig["danmaku_enabled"]) return;
  try {
    const _0x44f2eb = _0x325279["TeSZb"](
        _0x325279["laEsU"],
        _0x325279["AgLCz"](encodeURIComponent, playerConfig["videoUrl"]),
      ),
      _0x20caa0 = await _0x325279["WpMnM"](fetch, _0x44f2eb),
      _0x1577d7 = await _0x20caa0["json"]();
    if (Array["isArray"](_0x1577d7["data"])) {
      if (_0x325279["qQkrU"] !== _0x325279["xGyJp"]) {
        const _0x581105 = 0x7d0;
        let _0x26aa99 = [];
        for (let _0xd3b1c9 = 0x0; _0x325279["FrDvz"](_0xd3b1c9, _0x1577d7["data"]["length"]); _0xd3b1c9 += _0x581105) {
          if (_0x325279["SnAaX"]("CIfVT", _0x325279["zlYpu"])) {
            const _0x3396f5 = _0x1577d7["data"]
              ["slice"](_0xd3b1c9, _0x325279["TeSZb"](_0xd3b1c9, _0x581105))
              ["map"]((_0x1d47be) => {
                const _0x2d33c5 = _0x122903;
                if (_0x325279["ewEwP"]("QAAFq", "Rvufs")) {
                  const _0x1c525c = _0x325279["HtfGm"](_0x1d47be[0x0], undefined) ? _0x1d47be[0x0] : _0x1d47be["time"],
                    _0x577465 = _0x1d47be[0x1] !== undefined ? _0x1d47be[0x1] : _0x1d47be["mode"],
                    _0x5522ee = _0x325279["xtWvh"](_0x1d47be[0x2], undefined) ? _0x1d47be[0x2] : _0x1d47be["color"],
                    _0x48a034 = _0x325279["nZcbe"](_0x1d47be[0x4], undefined) ? _0x1d47be[0x4] : _0x1d47be["text"];
                  return {
                    time: _0x325279["AgLCz"](parseFloat, _0x1c525c) || 0x0,
                    mode: _0x325279["SnAaX"](_0x577465, "top")
                      ? 0x1
                      : _0x325279["SnAaX"](_0x577465, _0x325279["ycALt"])
                        ? 0x2
                        : 0x0,
                    color: _0x5522ee || _0x325279["TpyZI"],
                    text: _0x325279["AsUer"](_0x48a034, "")["trim"](),
                    border: ![],
                  };
                } else {
                  if (_0x2c92c9["includes"](_0x325279["MuSUQ"])) _0x2a8747 = _0x325279["aqaBF"];
                  else {
                    if (_0x33c1e["includes"](_0x325279["mUDFj"])) _0x118454 = _0x325279["GvxWL"];
                    else {
                      if (_0x175b68["includes"](_0x325279["GeBGM"])) _0x6fa8d8 = _0x325279["thHrp"];
                    }
                  }
                }
              })
              ["filter"]((_0x2a6374) => _0x2a6374["text"]);
            _0x26aa99 = _0x26aa99["concat"](_0x3396f5);
            if (_0x325279["FrDvz"](_0x325279["TeSZb"](_0xd3b1c9, _0x581105), _0x1577d7["data"]["length"])) {
              if (_0x325279["nQVmL"]("qPhsj", "amxXk")) await new Promise((_0x4fb73d) => setTimeout(_0x4fb73d, 0x0));
              else {
                const _0x2396fd = {
                  GTVge: function (_0x645227, _0x5a4c0a, _0x2b75d2) {
                    return _0x325279["nrYln"](_0x645227, _0x5a4c0a, _0x2b75d2);
                  },
                  LAINd: _0x325279["mRUQP"],
                };
                if (_0x325279["Qgpbk"](_0x189328["value"], "custom")) {
                  const _0x285a86 = _0x256183["skipOutro"] ? _0x325279["TeSZb"](_0x231298["skipOutro"], "秒") : "关闭";
                  return (
                    _0x325279["cLJRM"](_0x1bbda5, _0x325279["RYErT"], _0x580297["skipOutro"] || 0x0, (_0x5bf1ac) => {
                      const _0x29eb82 = _0x122903;
                      ((_0x35445e["skipOutro"] = _0x5bf1ac), _0x1c1c8f["setItem"]("art_skip_outro", _0x5bf1ac));
                      const _0xdeaf8e = _0x5bf1ac ? _0x5bf1ac + "秒" : "关闭";
                      (_0x2396fd["GTVge"](_0xa1204b, _0x2396fd["LAINd"], _0xdeaf8e),
                        (_0x481989["notice"]["show"] = "已设置跳过片尾 " + _0x5bf1ac + "\x20秒"));
                    }),
                    _0x285a86
                  );
                }
                return (
                  (_0x297cfb["skipOutro"] = _0x2a20fe["value"]),
                  _0x3ca3b4["setItem"](_0x325279["LVJHy"], _0x57dc9b["value"]),
                  _0x2814ba["html"]
                );
              }
            }
          } else _0x1e98be(_0x41703c["error"]);
        }
        if (_0x325279["IkWYf"](_0x26aa99["length"], MAX_DANMAKU)) {
          _0x26aa99["sort"]((_0x2e75a5, _0x54d433) => _0x2e75a5["time"] - _0x54d433["time"]);
          const _0x5c830a = _0x325279["GwdLj"](_0x26aa99["length"], MAX_DANMAKU),
            _0x12d210 = [];
          for (let _0x208148 = 0x0; _0x325279["FrDvz"](_0x208148, MAX_DANMAKU); _0x208148++) {
            _0x12d210["push"](
              _0x26aa99[
                Math["min"](Math["floor"](_0x208148 * _0x5c830a), _0x325279["mNuEe"](_0x26aa99["length"], 0x1))
              ],
            );
          }
          ((_0x26aa99 = _0x12d210),
            console["log"](_0x325279["aiPil"], MAX_DANMAKU, _0x325279["JADKy"], _0x1577d7["data"]["length"], "条）"));
        }
        if (art && art["plugins"] && art["plugins"]["artplayerPluginDanmuku"]) {
          if (_0x325279["ewEwP"]("wgwrL", _0x325279["gzyot"])) {
            const _0x837543 = { CFOHg: "API unavailable" };
            return new _0x22dfb6((_0x58b984, _0x477d42) => {
              const _0x31b703 = _0x122903;
              _0x2d4f74["orientation"] && _0xd68c39["orientation"]["lock"]
                ? _0x509dc2["orientation"]["lock"](_0x5c83af)["then"](_0x58b984)["catch"](_0x477d42)
                : _0x477d42(new _0x4b914a(_0x837543["CFOHg"]));
            });
          } else
            try {
              _0x325279["UfIMw"]("fERbX", _0x325279["NvBom"])
                ? _0x325279["AgLCz"](_0x4d9d42, _0x320fee)
                : (art["plugins"]["artplayerPluginDanmuku"]["config"]({ danmuku: _0x26aa99 }),
                  art["plugins"]["artplayerPluginDanmuku"]["load"](),
                  console["log"]("弹幕加载成功，共", _0x26aa99["length"], "条"));
            } catch (_0x3b0419) {
              console["error"](_0x325279["XbdJC"], _0x3b0419);
            }
        } else {
          if ("KcEhb" === "KcEhb") {
            console["error"]("未找到弹幕插件实例，请检查插件是否正确初始化");
            if (art) console["log"](_0x325279["UzFsl"], art["plugins"]);
          } else _0x325279["nrYln"](_0x9dc237, _0x272415["url"], _0x30c07b["type"]);
        }
      } else _0x187e4a(new _0x459f3f(_0x325279["pipBJ"]));
    } else console["warn"](_0x325279["pHFvp"], _0x1577d7);
  } catch (_0x5c9df4) {
    console["error"](_0x325279["qoWUI"], _0x5c9df4);
  }
}
var version_ = "jsjiami.com.v7";
