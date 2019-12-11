from default import put_file, settings

if __name__ == "__main__":
    while 1:
        source = put_file.path_unify(input())
        put_file.put_file(file_path=source,
                          repo_name=settings.image_repo_name, remote_name_setting=8)
        print("========== Finished. ==========")
