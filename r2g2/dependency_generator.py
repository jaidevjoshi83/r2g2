import requests
from packaging import version
import argparse

def check_package(channel, package_name):
    url = f"https://api.anaconda.org/package/{channel}/{package_name}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None


def find_closest_version(available_versions, target_version):
    versions = sorted(available_versions, key=version.parse, reverse=True)
    for v in versions:
        if version.parse(v) <= version.parse(target_version):
            return v
    return versions[0] if versions else None

def generate_galaxy_dependency_tag(package_name, version_str):
    return f'<requirement type="package" version="{version_str}">{package_name}</requirement>'

def return_galax_tag(package_name, package_version, dep_info=False):
    r_package = package_name
    target_version = package_version

    prefixes = ["bioconductor-", "r-"]
    channels = ["bioconda", "conda-forge"]

    if dep_info:
        print(dep_info, "34")
        for prefix in prefixes:
                conda_package = f"{prefix}{r_package.lower()}"
                for channel in channels:
                    result = check_package(channel, conda_package)
                    if result:
                        available_versions = [f['version'] for f in result['files']]
                        closest_version = find_closest_version(available_versions, target_version)
                        if closest_version:
                            print("39", closest_version,    conda_package)
                            dep_tag = generate_galaxy_dependency_tag(conda_package, closest_version)
                            return dep_tag
    else:
        return generate_galaxy_dependency_tag(package_name, package_version)
            
    # if neither prefix finds anything in any channel
    raise ValueError(f"No conda package found for {r_package} in bioconda/conda-forge under 'bioconductor-' or 'r-' prefixes.")

def detect_package_channel(dep):
    if check_package('bioconda', 'bioconductor-'+dep[0].lower()):
        return 'bioconductor-'+dep[0].lower(), dep[1]
    elif check_package('conda-forge', 'r-'+dep[0].lower()):
        return 'r-'+dep[0].lower(), dep[1]
    else:
        return dep[0].lower(), dep[1]

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--package_name', required=True, help="Provide R package name")
    parser.add_argument('-v', '--package_version', required=False, default='1.0.0')
    args = parser.parse_args()

    try:
        print(return_galax_tag(args.package_name, args.package_version))
    except ValueError as e:
        print(e)
