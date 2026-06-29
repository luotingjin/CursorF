from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file
from dotenv import load_dotenv

from tapd_testcase.service import GenerateRequest, run_generate

load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")
OUTPUT_ROOT = Path(__file__).resolve().parent.parent / "output" / "web"


@app.get("/")
def index():
    defaults = {
        "client_id": os.getenv("TAPD_CLIENT_ID", ""),
        "workspace_id": os.getenv("TAPD_WORKSPACE_ID", ""),
        "creator": os.getenv("TAPD_CREATOR", ""),
    }
    return render_template("index.html", defaults=defaults)


@app.post("/api/generate")
def api_generate():
    data = request.get_json(silent=True) or request.form

    required = ["client_id", "client_secret", "workspace_id", "story_id", "creator"]
    missing = [f for f in required if not str(data.get(f, "")).strip()]
    if missing:
        return jsonify({"success": False, "error": f"请填写必填项：{', '.join(missing)}"}), 400

    req = GenerateRequest(
        client_id=str(data["client_id"]).strip(),
        client_secret=str(data["client_secret"]).strip(),
        workspace_id=str(data["workspace_id"]).strip(),
        story_id=str(data["story_id"]).strip(),
        creator=str(data["creator"]).strip(),
        category=str(data.get("category", "")).strip(),
        generator_mode=str(data.get("generator_mode", "auto")).strip(),
        max_cases_per_story=int(data.get("max_cases_per_story", 8)),
        import_to_tapd=str(data.get("import_to_tapd", "true")).lower() in ("1", "true", "yes", "on"),
        output_dir=str(OUTPUT_ROOT),
    )

    result = run_generate(req)
    if not result.success:
        return jsonify({"success": False, "error": result.error}), 400

    return jsonify(
        {
            "success": True,
            "story_id": result.story_id,
            "story_short_id": result.story_short_id,
            "story_name": result.story_name,
            "creator": result.creator,
            "generated_count": result.generated_count,
            "imported_count": result.imported_count,
            "tcase_ids": result.tcase_ids,
            "csv_download": f"/download?path={result.csv_path}",
            "test_cases": result.test_cases,
        }
    )


@app.get("/download")
def download():
    path = request.args.get("path", "")
    file_path = Path(path).resolve()
    output_root = OUTPUT_ROOT.resolve()
    if not str(file_path).startswith(str(output_root)) or not file_path.exists():
        return jsonify({"error": "文件不存在"}), 404
    return send_file(file_path, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
