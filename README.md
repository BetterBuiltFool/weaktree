<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a id="readme-top"></a>
<!--
*** Thanks for checking out the Best-README-Template. If you have a suggestion
*** that would make this better, please fork the repo and create a pull request
*** or simply open an issue with the tag "enhancement".
*** Don't forget to give the project a star!
*** Thanks again! Now go create something AMAZING! :D
-->



<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
<!--
[![LinkedIn][linkedin-shield]][linkedin-url]
-->



<!-- PROJECT LOGO -->
<br />
<!--
<div align="center">
  <a href="https://github.com/BetterBuiltFool/weaktree">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a>
-->

<h3 align="center">Weaktree</h3>

  <p align="center">
    Model Data Trees Without Worrying About Lifetimes
    <br />
    <a href="https://github.com/BetterBuiltFool/weaktree"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <!--
    <a href="https://github.com/BetterBuiltFool/weaktree">View Demo</a>
    ·
    -->
    <a href="https://github.com/BetterBuiltFool/weaktree/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    ·
    <a href="https://github.com/BetterBuiltFool/weaktree/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
      <ul>
        <li><a href="#creating-weaktrees">Creating WeakTrees</a></li>
        <li><a href="#accessing-data">Accessing Data</a></li>
        <li><a href="#cleanup">Cleanup</a></li>
        <li><a href="#tree-iteration">Tree Iteration</a></li>
      </ul>
    <li><a href="#api-reference">API Reference</a></li>
    <!-- <li><a href="#roadmap">Roadmap</a></li> -->
    <!--<li><a href="#contributing">Contributing</a></li>-->
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <!-- <li><a href="#acknowledgments">Acknowledgments</a></li> -->
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

<!--
[![Product Name Screen Shot][product-screenshot]](https://example.com)
-->

Weaktree provides tree nodes that don't make strong references to their data, and can clean themselves up when their data expires. WeakTreeNodes also provide several handy iteration method for easy traversal.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- GETTING STARTED -->
## Getting Started

Weaktree is written in pure python, with no system dependencies, and should be OS-agnostic.

### Installation

Weaktree can be installed from the [PyPI][pypi-url] using [pip][pip-url]:

```sh
pip install weaktree
```

and can be imported for use with:
```python
import weaktree
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

Trees are built out of WeakTreeNodes. WeakTreeNodes possess a `trunk` and `branches`, which are used to define the hierarchy of the tree. Nodes with a trunk of `None` are considered root nodes.

### Creating WeakTrees

Root nodes can be created with the WeakTreeNode constructor.

```python
root = WeakTreeNode(some_object)
```

Branches can be added either by creating new nodes the same way and passing another node as the `trunk`, or by using WeakTreeNode.add_branch().

```python
root.add_branch(another_object)
```

WeakTreeNode.add_branch() returns the new node, so they can be chained.

```python
root.add_branch(third_object).add_branch(fourth_object).add_branch(fifth_object)
```

Trees can also be reorganized by assigning to the `trunk` property.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Accessing Data

The stored data of a Node is accessed by the `data` property. This will dereference the weakref, and return either the data object, or None if the object has expired.

Alternatively, if iterating over the tree by the `values()` method, the iterand will be the value from `data`.



<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Cleanup

WeakTreeNodes possess the `cleanup_mode` property. This is used to how the tree modifies itself when a Node's data reference expires. These values are accessible as constants in the WeakTreeNode class.

#### Prune

When the node expires, all descending nodes are removed from the tree.

Note: If there are strong references to those nodes elsewhere, they will be kept alive and the branches will not be fully unwound. However, they will no longer be reachable from other nodes in the tree.

#### Reparent

When the node expires, shift its branches up to its trunk. All descending nodes will be shifted up in the hierarchy.

#### No cleanup

When a node expires, leave the tree intact. Instead, the node will be "empty" and report a value of `None`.

#### Default

A node will do whatever its trunk node would do when it expires. For root nodes, this will be `prune`.


#### Callbacks

WeakTreeNodes feature an optional callback parameter for each node. The callback must take a weakreference object as its parameter. This will be the reference to the data value, just before it expires.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Tree Iteration

WeakTreeNodes provide several features to simplify traversal. All branch iteration follows insertion order of the branch nodes.

You can control the type of data provided in the iteration:

#### By Nodes

By using WeakTreeNode.nodes() or by directly iteration over the tree, you can traverse over the nodes themselves.
This is comparable to the `keys()` method of dictionaries.

Example:
```python
root = WeakTreeNode(some_object)

root.add_branch(one_fish).add_branch(two_fish)

root.add_branch(red_fish).add_branch(blue_fish)

for node in root.nodes():  # <- Same as `for node in root:`
    print(node)

    # Expected order: Node(some_object), Node(one_fish), Node(red_fish), Node(two_fish), Node(blue_fish)

```

#### By Values

By using WeakTreeNode.values(), you can iterate over the values of the nodes. This is comparable to the method of the same name in dictionaries.

Example:
```python
root = WeakTreeNode(some_object)

root.add_branch(one_fish).add_branch(two_fish)

root.add_branch(red_fish).add_branch(blue_fish)

for node in root.values():
    print(node)

    # Expected output: some_object, one_fish, red_fish, two_fish, blue_fish

```


#### By Items

WeakTreeNode.items() provides an iterable that gives the pairs of nodes and values. This is comparable to the method of the same name in dictionaries.


You can also control _how_ the iteration traverses the tree.

#### By Breadth

By using the `breadth()` method of any iterable, or directly iterating over one, you can specify that the traversal should happen in a breadth-first order, i.e. all nodes of the same level in the hierarchy are processed before moving on to the next level.

Example:
```python
root = WeakTreeNode(some_object)

root.add_branch(one_fish).add_branch(two_fish)

root.add_branch(red_fish).add_branch(blue_fish)

for node in root.nodes().breadth():  # <- Same as `for node in root:`
    print(node)

    # Expected order: Node(some_object), Node(one_fish), Node(red_fish), Node(two_fish), Node(blue_fish)

```

#### By Depth

By using the `depth()` method of any iterable, you can specify that the traversal should happen in a dpeth-first order, i.e. branches are followed to their furthest reaches before moving on to side branches.

Example:
```python
root = WeakTreeNode(some_object)

root.add_branch(one_fish).add_branch(two_fish)

root.add_branch(red_fish).add_branch(blue_fish)

for node in root.nodes().depth():
    print(node)

    # Expected order: Node(some_object), Node(one_fish), Node(two_fish), Node(red_fish), Node(blue_fish)

```

#### Towards the Root

By using the `towards_root()` method of any iterable, you can iterate towards the root of the tree.

Example:
```python
root = WeakTreeNode(some_object)

two_fish_node = root.add_branch(one_fish).add_branch(two_fish)

root.add_branch(red_fish).add_branch(blue_fish)

for node in two_fish_node.nodes().towards_root():
    print(node)

    # Expected order: Node(two_fish), Node(one_fish), Node(some_object)

```



<p align="right">(<a href="#readme-top">back to top</a>)</p>

## API Reference

```python
class weaktree.WeakTreeNode(data: Any, trunk: WeakTreeNode | None, cleanup_mode: CleanupMode, callback: Callable | None)
```

The base unit of a weak tree. Stores a weak reference to its data, and cleans itself up per the cleanup mode when that data expires. If a callback is provided, that will be called when the reference expires as well.

```python
method __init__(data: Any, trunk: WeakTreeNode | None, cleanup_mode: CleanupMode, callback: Callable | None) -> None
```

Creates a new WeakTreeNode, storing the passed _data_, and as a branch of _trunk_, if trunk is provided. Optionally, cleanup mode can be specified to determine how the node will behave when the data expires. Additionally, the optional callback can allow further customization of cleanup behavior.

```python
property branches: set[WeakTreeNode]
```

Read-only.

A set representing any branches that descend from the node. 

```python
property cleanup_mode: CleanupMode
```

An enum value that determines how the node will clenaup after itself when its data expires.

```python
property data: Any | None
```

The stored data. When called, dereferences and returns either a strong reference to the data, or None if the data has expired.

```python
property trunk: WeakTreeNode | Node
```

The previous node in the tree. If `None`, the node is considered a root.

```python
add_branch(data: Any, cleanup_mode: CleanupMode, callback: Callable | None) -> WeakTreeNode
```

Creates a new node as a branch of the calling node.

```python
breadth() -> Iterator[WeakTreeNode]
```

Returns an iterator that will traverse the tree by nodes, in a breadth-first pattern, starting at the calling node. Branches will be traversed in insertion order.


```python
depth() -> Iterator[WeakTreeNode]
```

Returns an iterator that will traverse the tree by nodes, in a depth-first pattern, starting at the calling node. Branches will be traversed in insertion order.

```python
towards_root() -> Iterator[WeakTreeNode]
```

Returns an iterator that will traverse the tree by nodes, up to the root, starting at the calling node.

```python
nodes() -> NodeIterable
```

Creates an iterable that allows for traversing the tree by nodes. Has the same breadth(), depth(), and towards_root() methods as WeakTreeNode

```python
values() -> ValueIterable
```

Creates an iterable that allows for traversing the tree by data values. Has the same breadth(), depth(), and towards_root() methods as WeakTreeNode

```python
items() -> ItemsIterable
```

Creates an iterable that allows for traversing the tree by node/value pairs. Has the same breadth(), depth(), and towards_root() methods as WeakTreeNode



<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ROADMAP -->
<!-- ## Roadmap

- [ ] (Eternal) Improve the renderer. Faster rendering means more renderables! -->

<!--
- [ ] Feature 2
- [ ] Feature 3
    - [ ] Nested Feature
-->

<!-- See the [open issues](https://github.com/BetterBuiltFool/weaktree/issues) for a full list of proposed features (and known issues). -->

<!-- <p align="right">(<a href="#readme-top">back to top</a>)</p> -->



<!-- CONTRIBUTING -->
<!--
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Top contributors:

<a href="https://github.com/BetterBuiltFool/weaktree/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=BetterBuiltFool/weaktree" alt="contrib.rocks image" />
</a>
-->



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Better Built Fool - betterbuiltfool@gmail.com

Bluesky - [@betterbuiltfool.bsky.social](https://bsky.app/profile/betterbuiltfool.bsky.social)
<!--
 - [@twitter_handle](https://twitter.com/twitter_handle)
-->

Project Link: [https://github.com/BetterBuiltFool/weaktree](https://github.com/BetterBuiltFool/weaktree)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
<!--## Acknowledgments

* []()
* []()
* []()

<p align="right">(<a href="#readme-top">back to top</a>)</p>
-->


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/BetterBuiltFool/weaktree.svg?style=for-the-badge
[contributors-url]: https://github.com/BetterBuiltFool/weaktree/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/BetterBuiltFool/weaktree.svg?style=for-the-badge
[forks-url]: https://github.com/BetterBuiltFool/weaktree/network/members
[stars-shield]: https://img.shields.io/github/stars/BetterBuiltFool/weaktree.svg?style=for-the-badge
[stars-url]: https://github.com/BetterBuiltFool/weaktree/stargazers
[issues-shield]: https://img.shields.io/github/issues/BetterBuiltFool/weaktree.svg?style=for-the-badge
[issues-url]: https://github.com/BetterBuiltFool/weaktree/issues
[license-shield]: https://img.shields.io/github/license/BetterBuiltFool/weaktree.svg?style=for-the-badge
[license-url]: https://github.com/BetterBuiltFool/weaktree/blob/main/LICENSE
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/linkedin_username
[product-screenshot]: images/screenshot.png
[Next.js]: https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white
[Next-url]: https://nextjs.org/
[python.org]: https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54
[python-url]: https://www.python.org/
[React.js]: https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB
[React-url]: https://reactjs.org/
[Vue.js]: https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vuedotjs&logoColor=4FC08D
[Vue-url]: https://vuejs.org/
[Angular.io]: https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white
[Angular-url]: https://angular.io/
[Svelte.dev]: https://img.shields.io/badge/Svelte-4A4A55?style=for-the-badge&logo=svelte&logoColor=FF3E00
[Svelte-url]: https://svelte.dev/
[Laravel.com]: https://img.shields.io/badge/Laravel-FF2D20?style=for-the-badge&logo=laravel&logoColor=white
[Laravel-url]: https://laravel.com
[Bootstrap.com]: https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white
[Bootstrap-url]: https://getbootstrap.com
[JQuery.com]: https://img.shields.io/badge/jQuery-0769AD?style=for-the-badge&logo=jquery&logoColor=white
[JQuery-url]: https://jquery.com 
[pypi-url]: https://pypi.org/project/weaktree
[pip-url]: https://pip.pypa.io/en/stable/