# import requests
# from packaging import version
# import argparse

# def check_package(channel, package_name):
#     url = f"https://api.anaconda.org/package/{channel}/{package_name}"
#     response = requests.get(url)
#     if response.status_code == 200:
#         return response.json()
#     else:
#         return None

# def find_closest_version(available_versions, target_version):
#     versions = sorted(available_versions, key=version.parse, reverse=True)
#     for v in versions:
#         if version.parse(v) <= version.parse(target_version):
#             return v
#     return versions[0] if versions else None

# def generate_galaxy_dependency_tag(package_name, channel, version_str):
#     return f'<requirement type="package" version="{version_str}">{package_name}</requirement>'

# def return_galax_tag(package_name, package_version):
#     # Example usage:
#     r_package = package_name
#     conda_package = f"r-{r_package.lower()}"
#     target_version = package_version

#     channels = ["bioconda", "conda-forge"]
#     for channel in channels:
#         result = check_package(channel, conda_package)
#         if result:
#             available_versions = [f['version'] for f in result['files']]
#             closest_version = find_closest_version(available_versions, target_version)
#             if closest_version:
#                 dep_tag = generate_galaxy_dependency_tag(conda_package, channel, closest_version)
#                 return dep_tag
#                 break
#     else:
#         print(f"No conda package found for {r_package} in specified channels.")


# if __name__=="__main__":

#     parser = argparse.ArgumentParser()
#     parser.add_argument('-p', '--package_name', required=True, help="Provide path of a R file... ")
#     parser.add_argument('-v', '--package_version', required=False, default='out')
#     args = parser.parse_args()
#     print(return_galax_tag(args.package_name, args.package_version))


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

def generate_galaxy_dependency_tag(package_name, channel, version_str):
    return f'<requirement type="package" version="{version_str}">{package_name}</requirement>'

def return_galax_tag(package_name, package_version):
    r_package = package_name
    target_version = package_version

    prefixes = ["bioconductor-", "r-"]
    channels = ["bioconda", "conda-forge"]

    for prefix in prefixes:
        conda_package = f"{prefix}{r_package.lower()}"
        for channel in channels:
            result = check_package(channel, conda_package)
            if result:
                available_versions = [f['version'] for f in result['files']]
                closest_version = find_closest_version(available_versions, target_version)
                if closest_version:
                    dep_tag = generate_galaxy_dependency_tag(conda_package, channel, closest_version)
                    print(dep_tag)
                    return dep_tag
        

    # if neither prefix finds anything in any channel
    raise ValueError(f"No conda package found for {r_package} in bioconda/conda-forge under 'bioconductor-' or 'r-' prefixes.")

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--package_name', required=True, help="Provide R package name")
    parser.add_argument('-v', '--package_version', required=False, default='1.0.0')
    args = parser.parse_args()

    try:
        print(return_galax_tag(args.package_name, args.package_version))
    except ValueError as e:
        print(e)
